import asyncio
import json
from collections import deque
from collections.abc import AsyncIterator
from dataclasses import dataclass
from itertools import count

from fastapi import Request


@dataclass(frozen=True)
class TradeEvent:
    event_id: int
    event_type: str
    payload: dict[str, object]


class EventBroker:
    def __init__(self) -> None:
        self._event_ids = count(1)
        self._history: deque[TradeEvent] = deque(maxlen=100)
        self._subscribers: set[asyncio.Queue[TradeEvent]] = set()

    async def publish(self, event_type: str, payload: dict[str, object]) -> TradeEvent:
        event = TradeEvent(next(self._event_ids), event_type, payload)
        self._history.append(event)
        for subscriber in tuple(self._subscribers):
            await subscriber.put(event)
        return event

    async def subscribe(self, last_event_id: int = 0) -> AsyncIterator[TradeEvent]:
        queue: asyncio.Queue[TradeEvent] = asyncio.Queue()
        self._subscribers.add(queue)
        try:
            for event in self._history:
                if event.event_id > last_event_id:
                    yield event
            while True:
                yield await queue.get()
        finally:
            self._subscribers.discard(queue)


broker = EventBroker()


def get_last_event_id(request: Request) -> int:
    value = request.headers.get("last-event-id", "0")
    try:
        return max(0, int(value))
    except ValueError:
        return 0


def format_sse(event: TradeEvent) -> str:
    return (
        f"id: {event.event_id}\n"
        f"event: {event.event_type}\n"
        f"data: {json.dumps(event.payload)}\n\n"
    )
