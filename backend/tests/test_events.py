import asyncio

import pytest

from app.services.events import EventBroker, format_sse


@pytest.mark.asyncio
async def test_broker_replays_events_after_last_event_id() -> None:
    broker = EventBroker()
    first = await broker.publish("ingestion.completed", {"job_id": 1})
    second = await broker.publish("ingestion.completed", {"job_id": 2})

    events = broker.subscribe(first.event_id)
    replayed = await asyncio.wait_for(anext(events), timeout=1)

    assert replayed.event_id == second.event_id
    assert replayed.payload == {"job_id": 2}
    await events.aclose()


def test_format_sse_includes_id_event_and_json_data() -> None:
    broker = EventBroker()

    async def publish_event():
        return await broker.publish("ingestion.completed", {"job_id": 4})

    event = asyncio.run(publish_event())
    message = format_sse(event)

    assert f"id: {event.event_id}" in message
    assert "event: ingestion.completed" in message
    assert 'data: {"job_id": 4}' in message
