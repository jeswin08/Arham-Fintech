from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import StreamingResponse
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.ingestion_job import IngestionJob
from app.models.trade import Trade
from app.schemas.job import IngestionJobResponse
from app.schemas.trade import (
    TradeListResponse,
    TradeRecord,
    TradeStatsResponse,
)
from app.workers.ingestion import create_ingestion_job, schedule_ingestion_job
from app.services.events import broker, format_sse, get_last_event_id

router = APIRouter(prefix="/api/trades", tags=["trades"])
DbSession = Annotated[Session, Depends(get_db)]


@router.get("/stream")
async def trade_stream(request: Request) -> StreamingResponse:
    async def event_generator():
        yield ": connected\nretry: 3000\n\n"
        async for event in broker.subscribe(get_last_event_id(request)):
            if await request.is_disconnected():
                break
            yield format_sse(event)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("", response_model=TradeListResponse)
def list_trades(
    db: DbSession,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
    symbol: str | None = Query(default=None, min_length=1, max_length=12),
    search: str | None = Query(default=None, min_length=1, max_length=80),
) -> TradeListResponse:
    filters = []
    if symbol:
        filters.append(Trade.symbol == symbol.upper())
    if search:
        search_pattern = f"%{search}%"
        filters.append(
            (Trade.trade_id.ilike(search_pattern))
            | (Trade.client.ilike(search_pattern))
            | (Trade.symbol.ilike(search_pattern))
        )

    total = db.scalar(select(func.count(Trade.id)).where(*filters)) or 0
    records = db.scalars(
        select(Trade)
        .where(*filters)
        .order_by(Trade.timestamp.desc(), Trade.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    return TradeListResponse(
        records=[TradeRecord.model_validate(record) for record in records],
        page=page,
        page_size=page_size,
        total=total,
    )


@router.post(
    "/pull",
    response_model=IngestionJobResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def start_trade_pull(
    db: DbSession,
    record_count: int = Query(default=2_000, ge=1, le=5_000),
    delay_seconds: float = Query(default=0, ge=0, le=900),
    seed: int = Query(default=2026, ge=0),
) -> IngestionJobResponse:
    job_id = create_ingestion_job(db)
    schedule_ingestion_job(
        job_id,
        record_count=record_count,
        delay_seconds=delay_seconds,
        seed=seed,
    )
    job = db.get(IngestionJob, job_id)
    if job is None:
        raise HTTPException(status_code=500, detail="Created ingestion job could not be loaded")
    return IngestionJobResponse.model_validate(job)


@router.get("/pull/{job_id}", response_model=IngestionJobResponse)
def get_pull_status(job_id: int, db: DbSession) -> IngestionJobResponse:
    job = db.get(IngestionJob, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail=f"Ingestion job {job_id} not found")
    return IngestionJobResponse.model_validate(job)


@router.get("/stats", response_model=TradeStatsResponse)
def get_trade_stats(db: DbSession) -> TradeStatsResponse:
    total_trades = db.scalar(select(func.count(Trade.id))) or 0
    unique_clients = db.scalar(select(func.count(func.distinct(Trade.client)))) or 0
    unique_symbols = db.scalar(select(func.count(func.distinct(Trade.symbol)))) or 0
    total_trade_value = db.scalar(
        select(func.coalesce(func.sum(Trade.quantity * Trade.price), 0.0))
    ) or 0.0
    return TradeStatsResponse(
        total_trades=total_trades,
        unique_clients=unique_clients,
        unique_symbols=unique_symbols,
        total_trade_value=round(float(total_trade_value), 2),
    )
