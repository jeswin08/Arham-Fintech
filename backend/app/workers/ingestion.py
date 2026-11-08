import asyncio
import logging
from collections.abc import Callable
from datetime import UTC, datetime

from sqlalchemy.orm import Session, sessionmaker

from app.database.session import SessionLocal
from app.models.ingestion_job import IngestionJob
from app.services.mock_bse import fetch_mock_trades
from app.services.persistence import save_trades
from app.services.events import broker

SessionFactory = Callable[[], Session]
logger = logging.getLogger(__name__)


def create_ingestion_job(db: Session) -> int:
    job = IngestionJob(status="pending")
    db.add(job)
    db.commit()
    db.refresh(job)
    return job.id


async def run_ingestion_job(
    job_id: int,
    *,
    record_count: int = 2_000,
    delay_seconds: float = 0,
    seed: int = 2026,
    session_factory: sessionmaker[Session] = SessionLocal,
) -> None:
    db = session_factory()
    try:
        job = db.get(IngestionJob, job_id)
        if job is None:
            raise ValueError(f"Ingestion job {job_id} does not exist")

        job.status = "running"
        job.started_at = datetime.now(UTC)
        db.commit()

        records = await fetch_mock_trades(
            record_count=record_count,
            delay_seconds=delay_seconds,
            seed=seed,
            ingestion_id=job_id,
        )
        processed_count = len(records)
        inserted_count = save_trades(db, records)

        job = db.get(IngestionJob, job_id)
        if job is None:
            raise ValueError(f"Ingestion job {job_id} disappeared during execution")
        job.status = "completed"
        job.completed_at = datetime.now(UTC)
        job.total_records = inserted_count
        job.total_records_processed = processed_count
        job.inserted_records = inserted_count
        db.commit()
        await broker.publish(
            "ingestion.completed",
            {
                "job_id": job.id,
                "status": job.status,
                "total_records": job.total_records,
                "total_records_processed": job.total_records_processed,
                "inserted_records": job.inserted_records,
                "completed_at": job.completed_at.isoformat(),
            },
        )
    except Exception as error:
        db.rollback()
        job = db.get(IngestionJob, job_id)
        if job is not None:
            job.status = "failed"
            job.completed_at = datetime.now(UTC)
            job.error_message = str(error)
            db.commit()
            await broker.publish(
                "ingestion.failed",
                {
                    "job_id": job.id,
                    "status": job.status,
                    "error_message": job.error_message,
                    "completed_at": job.completed_at.isoformat(),
                },
            )
        raise
    finally:
        db.close()


def schedule_ingestion_job(
    job_id: int,
    *,
    record_count: int = 2_000,
    delay_seconds: float = 0,
    seed: int = 2026,
) -> asyncio.Task[None]:
    """Schedule work on the current process without holding an HTTP request open."""
    task = asyncio.create_task(
        run_ingestion_job(
            job_id,
            record_count=record_count,
            delay_seconds=delay_seconds,
            seed=seed,
        )
    )
    task.add_done_callback(_report_task_failure)
    return task


def _report_task_failure(task: asyncio.Task[None]) -> None:
    if task.cancelled():
        return
    error = task.exception()
    if error is not None:
        logger.error("Ingestion job failed: %s", error, exc_info=error)
