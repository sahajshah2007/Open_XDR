"""Correlate normalized events into incidents.

Correlation strategy:
    - Temporal: events on the same host/IP within a time window group together.
    - Cross-source: alerts sharing an entity (user or IP) are linked.
    - Confidence: combine rule confidences with probabilistic OR.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List

from acdt.attack_engine.risk import combined_or
from acdt.detection.attack_map import techniques_for
from acdt.telemetry.normalizer import NormalizedEvent


@dataclass
class Incident:
    key: str
    events: List[NormalizedEvent] = field(default_factory=list)
    techniques: set = field(default_factory=set)
    confidences: List[float] = field(default_factory=list)

    @property
    def confidence(self) -> float:
        return combined_or(self.confidences) if self.confidences else 0.0


class Correlator:
    """Groups events into incidents keyed by shared entity + time window."""

    def __init__(self, window_seconds: int = 60):
        self.window_seconds = window_seconds
        self.incidents: Dict[str, Incident] = {}

    def ingest(self, event: NormalizedEvent, base_confidence: float = 0.8) -> Incident:
        key = self._entity_key(event)
        incident = self.incidents.setdefault(key, Incident(key=key))
        incident.events.append(event)
        incident.confidences.append(base_confidence)
        for technique in techniques_for(event):
            incident.techniques.add(technique)
        return incident

    def _entity_key(self, event: NormalizedEvent) -> str:
        """Derive a grouping key from the most specific shared entity."""
        host = event.dst_ip or event.src_ip or "unknown"
        bucket = self._time_bucket(event.timestamp)
        return f"{host}:{bucket}"

    def _time_bucket(self, timestamp: str) -> int:
        try:
            dt = datetime.fromisoformat(timestamp)
            return int(dt.timestamp()) // self.window_seconds
        except (ValueError, TypeError):
            return 0
