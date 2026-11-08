from datetime import datetime

from pydantic import BaseModel, Field


class TradeRecord(BaseModel):
    model_config = {"from_attributes": True}

    trade_id: str = Field(pattern=r"^BSE-\d{8}-(?:\d{6}|\d+-\d{6})$")
    client: str = Field(min_length=2, max_length=80)
    symbol: str = Field(pattern=r"^[A-Z0-9.-]{1,12}$")
    quantity: int = Field(gt=0)
    price: float = Field(gt=0)
    timestamp: datetime


class TradeFeedResponse(BaseModel):
    source: str
    generated_at: datetime
    records: list[TradeRecord]


class TradeListResponse(BaseModel):
    records: list[TradeRecord]
    page: int
    page_size: int
    total: int


class TradeStatsResponse(BaseModel):
    total_trades: int
    unique_clients: int
    unique_symbols: int
    total_trade_value: float
