from collections.abc import Iterable

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.trade import Trade
from app.schemas.trade import TradeRecord


def save_trades(db: Session, records: Iterable[TradeRecord]) -> int:
    trade_records = list(records)
    if not trade_records:
        return 0

    trade_ids = {record.trade_id for record in trade_records}
    existing_ids = set(
        db.scalars(select(Trade.trade_id).where(Trade.trade_id.in_(trade_ids))).all()
    )
    seen_ids = set(existing_ids)
    new_trades = []
    for record in trade_records:
        if record.trade_id in seen_ids:
            continue
        seen_ids.add(record.trade_id)
        new_trades.append(
            Trade(
                trade_id=record.trade_id,
                client=record.client,
                symbol=record.symbol,
                quantity=record.quantity,
                price=record.price,
                timestamp=record.timestamp,
            )
        )

    db.add_all(new_trades)
    db.commit()
    return len(new_trades)
