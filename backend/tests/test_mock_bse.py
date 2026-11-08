from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_mock_bse_returns_requested_trade_records() -> None:
    response = client.get("/getTrades?record_count=3&seed=7")

    assert response.status_code == 200
    payload = response.json()
    assert payload["source"] == "mock-bse"
    assert len(payload["records"]) == 3
    assert payload["records"][0]["trade_id"].startswith("BSE-")
    assert {"client", "symbol", "quantity", "price", "timestamp"} <= set(
        payload["records"][0]
    )


def test_mock_bse_is_deterministic_for_a_seed() -> None:
    first = client.get("/getTrades?record_count=2&seed=11").json()
    second = client.get("/getTrades?record_count=2&seed=11").json()

    assert first["records"] == second["records"]


def test_mock_bse_validates_request_limits() -> None:
    response = client.get("/getTrades?record_count=0")

    assert response.status_code == 422
