from datetime import UTC, datetime

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

from app.api.trades import router as trades_router
from app.core.config import settings
from app.database.session import create_database_tables
from app.schemas.trade import TradeFeedResponse
from app.services.mock_bse import fetch_mock_trades

app = FastAPI(
    title="ARHAM Fintech API",
    description="Backend for the ARHAM Fintech trade ingestion platform.",
    version="0.1.0",
)

create_database_tables()
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
app.include_router(trades_router)


@app.get("/health", tags=["system"])
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/getTrades", response_model=TradeFeedResponse, tags=["mock-bse"])
async def get_trades(
    record_count: int = Query(default=2_000, ge=1, le=5_000),
    delay_seconds: float = Query(default=0, ge=0, le=900),
    seed: int = Query(default=2026, ge=0),
) -> TradeFeedResponse:
    """Return a deterministic trade feed that simulates the BSE data source."""
    records = await fetch_mock_trades(
        record_count=record_count,
        delay_seconds=delay_seconds,
        seed=seed,
    )
    return TradeFeedResponse(
        source="mock-bse",
        generated_at=datetime.now(UTC).replace(microsecond=0),
        records=records,
    )
