from datetime import UTC, datetime

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database.session import Base, get_db
from app.main import app
from app.models.trade import Trade


engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
Base.metadata.create_all(engine)
SessionFactory = sessionmaker(bind=engine)


def override_get_db():
    with SessionFactory() as db:
        yield db


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


def setup_function() -> None:
    with SessionFactory() as db:
        db.query(Trade).delete()
        db.commit()


def test_list_trades_is_paginated_and_filterable() -> None:
    with SessionFactory() as db:
        db.add_all(
            [
                Trade(
                    trade_id="BSE-20260101-000001",
                    client="Apex Capital",
                    symbol="INFY",
                    quantity=100,
                    price=1500,
                    timestamp=datetime(2026, 1, 1, tzinfo=UTC),
                ),
                Trade(
                    trade_id="BSE-20260101-000002",
                    client="Vertex Holdings",
                    symbol="TCS",
                    quantity=200,
                    price=3900,
                    timestamp=datetime(2026, 1, 2, tzinfo=UTC),
                ),
            ]
        )
        db.commit()

    response = client.get("/api/trades?page=1&page_size=1&symbol=infy")

    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert response.json()["records"][0]["symbol"] == "INFY"


def test_stats_returns_aggregates() -> None:
    with SessionFactory() as db:
        db.add(
            Trade(
                trade_id="BSE-20260101-000003",
                client="Apex Capital",
                symbol="INFY",
                quantity=100,
                price=1500,
                timestamp=datetime(2026, 1, 1, tzinfo=UTC),
            )
        )
        db.commit()

    response = client.get("/api/trades/stats")

    assert response.status_code == 200
    assert response.json() == {
        "total_trades": 1,
        "unique_clients": 1,
        "unique_symbols": 1,
        "total_trade_value": 150000,
    }


def test_missing_job_returns_not_found() -> None:
    response = client.get("/api/trades/pull/999999")

    assert response.status_code == 404


def test_pull_returns_accepted_job() -> None:
    response = client.post(
        "/api/trades/pull?record_count=1&delay_seconds=0&seed=41"
    )

    assert response.status_code == 202
    assert response.json()["status"] == "pending"
