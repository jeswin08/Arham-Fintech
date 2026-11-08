import asyncio

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database.session import Base
from app.models.ingestion_job import IngestionJob
from app.models.trade import Trade
from app.services.events import EventBroker
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
async def test_failed_ingestion_is_persisted(session_factory, monkeypatch) -> None:
    async def fail_fetch(*args, **kwargs):
        raise RuntimeError("exchange unavailable")

    monkeypatch.setattr("app.workers.ingestion.fetch_mock_trades", fail_fetch)
    with session_factory() as db:
        job_id = create_ingestion_job(db)

    with pytest.raises(RuntimeError, match="exchange unavailable"):
        await run_ingestion_job(job_id, session_factory=session_factory)

    with session_factory() as db:
        job = db.get(IngestionJob, job_id)

    assert job is not None
    assert job.status == "failed"
    assert job.error_message == "exchange unavailable"
    assert job.completed_at is not None


@pytest.mark.asyncio
async def test_multiple_subscribers_receive_one_event() -> None:
    broker = EventBroker()
    first_subscriber = broker.subscribe()
    second_subscriber = broker.subscribe()
    first_waiter = asyncio.create_task(anext(first_subscriber))
    second_waiter = asyncio.create_task(anext(second_subscriber))
    await asyncio.sleep(0)

    published = await broker.publish("ingestion.completed", {"job_id": 12})
    first_event, second_event = await asyncio.gather(first_waiter, second_waiter)

    assert first_event == published
    assert second_event == published
    await first_subscriber.aclose()
    await second_subscriber.aclose()


@pytest.mark.asyncio
async def test_replayed_event_refreshes_after_reconnect() -> None:
    broker = EventBroker()
    published = await broker.publish("ingestion.completed", {"job_id": 13})
    reconnect = broker.subscribe(published.event_id - 1)

    replayed = await asyncio.wait_for(anext(reconnect), timeout=1)

    assert replayed.event_id == published.event_id
    await reconnect.aclose()


@pytest.mark.asyncio
async def test_completed_ingestion_persists_data_for_refresh(session_factory) -> None:
    with session_factory() as db:
        job_id = create_ingestion_job(db)

    await run_ingestion_job(
        job_id,
        record_count=3,
        seed=404,
        session_factory=session_factory,
    )

    with session_factory() as db:
        job = db.get(IngestionJob, job_id)
        trades = db.scalars(select(Trade)).all()

    assert job is not None and job.status == "completed"
    assert job.total_records == 3
    assert job.total_records_processed == 3
    assert job.inserted_records == 3
    assert len(trades) == 3


@pytest.mark.asyncio
async def test_duplicate_ingestion_reports_processed_and_inserted_counts(session_factory) -> None:
    with session_factory() as db:
        first_job_id = create_ingestion_job(db)

    await run_ingestion_job(
        first_job_id,
        record_count=3,
        seed=505,
        session_factory=session_factory,
    )

    await run_ingestion_job(
        first_job_id,
        record_count=3,
        seed=505,
        session_factory=session_factory,
    )

    with session_factory() as db:
        job = db.get(IngestionJob, first_job_id)

    assert job is not None
    assert job.total_records_processed == 3
    assert job.inserted_records == 0
