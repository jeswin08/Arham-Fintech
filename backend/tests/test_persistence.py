from datetime import UTC, datetime

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database.session import Base
from app.models.trade import Trade
from app.schemas.trade import TradeRecord
from app.services.persistence import save_trades


def test_save_trades_persists_records_and_skips_duplicates() -> None:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine)

    records = [
        TradeRecord(
            trade_id="BSE-20260101-000001",
            client="Apex Capital",
            symbol="INFY",
            quantity=100,
            price=1500.25,
            timestamp=datetime(2026, 1, 1, tzinfo=UTC),
        )
    ]

    with session_factory() as db:
        assert save_trades(db, records + records) == 1
        assert save_trades(db, records) == 0
        saved = db.scalars(select(Trade)).all()

    assert len(saved) == 1
    assert saved[0].trade_id == records[0].trade_id
