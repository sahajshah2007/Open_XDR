"""Automate multi-attack evaluation runs and compute metrics.

Metrics collected per scenario run:
    - detected (bool), detect_time (s)
    - contained (bool), contain_time (s)
    - false_alerts (int)

Aggregate metrics: MTTD, MTTC, precision, recall, containment rate.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from statistics import mean
from typing import List, Optional


@dataclass
class TrialResult:
    scenario: str
    detected: bool
    detect_time: Optional[float] = None
    contained: bool = False
    contain_time: Optional[float] = None
    false_alerts: int = 0


@dataclass
class EvaluationReport:
    trials: List[TrialResult] = field(default_factory=list)

    def add(self, result: TrialResult) -> None:
        self.trials.append(result)

    @property
    def mttd(self) -> float:
        times = [t.detect_time for t in self.trials if t.detected and t.detect_time is not None]
        return mean(times) if times else 0.0

    @property
    def mttc(self) -> float:
        times = [t.contain_time for t in self.trials if t.contained and t.contain_time is not None]
        return mean(times) if times else 0.0

    @property
    def detection_rate(self) -> float:
        return self._rate(t.detected for t in self.trials)

    @property
    def containment_rate(self) -> float:
        return self._rate(t.contained for t in self.trials)

    def _rate(self, flags) -> float:
        flags = list(flags)
        return sum(flags) / len(flags) if flags else 0.0

    def summary(self) -> dict:
        return {
            "trials": len(self.trials),
            "mttd_seconds": round(self.mttd, 3),
            "mttc_seconds": round(self.mttc, 3),
            "detection_rate": round(self.detection_rate, 3),
            "containment_rate": round(self.containment_rate, 3),
        }
