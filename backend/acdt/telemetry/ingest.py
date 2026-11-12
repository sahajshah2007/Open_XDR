"""Consume normalized telemetry from the message bus and update the twin.

The ingest loop subscribes to a Redis Stream, normalizes each raw event, and
hands it to the graph updater and detection engine.
"""
from __future__ import annotations

import json
from typing import Callable, Iterable

from acdt.telemetry.normalizer import NormalizedEvent, normalize


def publish(redis_client, stream: str, source: str, event: dict) -> str:
    """Publish a raw telemetry event onto the stream (tagged by source)."""
    return redis_client.xadd(
        stream, {"source": source, "event": json.dumps(event)}
    )


def consume(
    redis_client,
    stream: str,
    handler: Callable[[NormalizedEvent], None],
    last_id: str = "0",
    count: int = 100,
) -> str:
    """Read a batch from the stream, normalize, and invoke handler per event.

    Returns the last-seen stream id so the caller can continue from there.
    """
    entries = redis_client.xread({stream: last_id}, count=count)
    for _stream, messages in entries or []:
        for msg_id, fields in messages:
            source = _decode(fields.get(b"source", fields.get("source")))
            raw = _decode(fields.get(b"event", fields.get("event")))
            event = json.loads(raw)
            handler(normalize(source, event))
            last_id = _decode(msg_id)
    return last_id


def replay(events: Iterable[tuple[str, dict]], handler: Callable[[NormalizedEvent], None]) -> None:
    """Offline helper: normalize an in-memory (source, event) iterable."""
    for source, event in events:
        handler(normalize(source, event))


def _decode(value):
    if isinstance(value, bytes):
        return value.decode()
    return value
