import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database.session import Base
from app.models.ingestion_job import IngestionJob
from app.models.trade import Trade
from app.workers.ingestion import create_ingestion_job, run_ingestion_job


@pytest.fixture
def session_factory() -> sessionmaker:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)


@pytest.mark.asyncio
async def test_worker_completes_job_and_persists_trades(session_factory) -> None:
    with session_factory() as db:
        job_id = create_ingestion_job(db)

    await run_ingestion_job(
        job_id,
        record_count=4,
        seed=17,
        session_factory=session_factory,
    )

    with session_factory() as db:
        job = db.get(IngestionJob, job_id)
        trades = db.scalars(select(Trade)).all()

    assert job is not None
    assert job.status == "completed"
    assert job.started_at is not None
    assert job.completed_at is not None
    assert job.total_records == 4
    assert job.total_records_processed == 4
    assert job.inserted_records == 4
    assert len(trades) == 4


@pytest.mark.asyncio
async def test_worker_reports_missing_job(session_factory) -> None:
    with pytest.raises(ValueError, match="does not exist"):
        await run_ingestion_job(999, session_factory=session_factory)


@pytest.mark.asyncio
async def test_consecutive_jobs_insert_all_records(session_factory) -> None:
    with session_factory() as db:
        first_job_id = create_ingestion_job(db)
        second_job_id = create_ingestion_job(db)

    await run_ingestion_job(
        first_job_id,
        record_count=2_000,
        seed=2026,
        session_factory=session_factory,
    )
    await run_ingestion_job(
        second_job_id,
        record_count=2_000,
        seed=2026,
        session_factory=session_factory,
    )

    with session_factory() as db:
        first_job = db.get(IngestionJob, first_job_id)
        second_job = db.get(IngestionJob, second_job_id)
        trades = db.scalars(select(Trade)).all()

    assert first_job is not None and first_job.inserted_records == 2_000
    assert second_job is not None and second_job.inserted_records == 2_000
    assert len(trades) == 4_000
