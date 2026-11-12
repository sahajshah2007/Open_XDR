"""Normalize heterogeneous telemetry into a common event schema.

Common schema:
    {
        "timestamp": <ISO8601 str>,
        "source": "zeek" | "falco" | "wazuh" | "attacker",
        "event_type": <str>,
        "src_ip": <str | None>,
        "dst_ip": <str | None>,
        "payload": <dict>,   # original event
    }
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any, Optional


@dataclass
class NormalizedEvent:
    timestamp: str
    source: str
    event_type: str
    src_ip: Optional[str] = None
    dst_ip: Optional[str] = None
    payload: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)


def _iso(ts: Any) -> str:
    """Convert an epoch float or passthrough string into ISO8601."""
    if isinstance(ts, (int, float)):
        return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()
    if isinstance(ts, str):
        return ts
    return datetime.now(tz=timezone.utc).isoformat()


def normalize_zeek(event: dict) -> NormalizedEvent:
    """Normalize a Zeek conn/http log line."""
    return NormalizedEvent(
        timestamp=_iso(event.get("ts")),
        source="zeek",
        event_type=event.get("service") or event.get("proto") or "zeek",
        src_ip=event.get("id.orig_h"),
        dst_ip=event.get("id.resp_h"),
        payload=event,
    )


def normalize_falco(event: dict) -> NormalizedEvent:
    """Normalize a Falco JSON alert."""
    return NormalizedEvent(
        timestamp=_iso(event.get("time")),
        source="falco",
        event_type=event.get("rule", "falco_alert"),
        payload=event,
    )


def normalize_wazuh(event: dict) -> NormalizedEvent:
    """Normalize a Wazuh JSON alert."""
    rule = event.get("rule", {})
    return NormalizedEvent(
        timestamp=_iso(event.get("timestamp")),
        source="wazuh",
        event_type=rule.get("description", "wazuh_alert"),
        payload=event,
    )


def normalize_attacker(event: dict) -> NormalizedEvent:
    """Normalize a synthetic attacker-simulation event."""
    return NormalizedEvent(
        timestamp=_iso(event.get("time")),
        source="attacker",
        event_type=event.get("action", "attacker_event"),
        src_ip=event.get("attacker_ip"),
        dst_ip=event.get("target"),
        payload=event,
    )


_DISPATCH = {
    "zeek": normalize_zeek,
    "falco": normalize_falco,
    "wazuh": normalize_wazuh,
    "attacker": normalize_attacker,
}


def normalize(source: str, event: dict) -> NormalizedEvent:
    """Dispatch to the correct normalizer based on source."""
    fn = _DISPATCH.get(source)
    if fn is None:
        raise ValueError(f"unknown telemetry source: {source}")
    return fn(event)
