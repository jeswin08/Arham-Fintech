import asyncio
import random
from datetime import UTC, datetime, timedelta

from app.schemas.trade import TradeRecord

CLIENTS = (
    "Apex Capital",
    "BlueRiver Investments",
    "Cedar Wealth",
    "Northstar Brokers",
    "Summit Trading",
    "Vertex Holdings",
)

SYMBOL_PRICES = {
    "INFY": 1_512.40,
    "RELIANCE": 2_846.75,
    "TCS": 3_925.10,
    "HDFCBANK": 1_684.30,
    "ICICIBANK": 1_237.85,
    "SBIN": 824.60,
    "ITC": 463.25,
    "LT": 3_486.90,
}


async def fetch_mock_trades(
    record_count: int,
    delay_seconds: float,
    seed: int,
    ingestion_id: int | None = None,
) -> list[TradeRecord]:
    if delay_seconds:
        await asyncio.sleep(delay_seconds)

    generator = random.Random(seed)
    timestamp = datetime(2026, 1, 1, tzinfo=UTC) + timedelta(days=seed % 365)
    symbols = tuple(SYMBOL_PRICES)

    return [
        _create_trade(
            sequence=index,
            generator=generator,
            timestamp=timestamp - timedelta(seconds=record_count - index),
            symbols=symbols,
            ingestion_id=ingestion_id,
        )
        for index in range(1, record_count + 1)
    ]


def _create_trade(
    sequence: int,
    generator: random.Random,
    timestamp: datetime,
    symbols: tuple[str, ...],
    ingestion_id: int | None,
) -> TradeRecord:
    symbol = generator.choice(symbols)
    base_price = SYMBOL_PRICES[symbol]
    price = round(base_price * (1 + generator.uniform(-0.02, 0.02)), 2)

    return TradeRecord(
        trade_id=(
            f"BSE-{timestamp:%Y%m%d}-{sequence:06d}"
            if ingestion_id is None
            else f"BSE-{timestamp:%Y%m%d}-{ingestion_id:06d}-{sequence:06d}"
        ),
        client=generator.choice(CLIENTS),
        symbol=symbol,
        quantity=generator.randint(1, 500) * 10,
        price=price,
        timestamp=timestamp,
    )
