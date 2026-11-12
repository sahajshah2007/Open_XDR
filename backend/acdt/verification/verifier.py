"""Verify that a response action contained the threat.

Checks are probe-based: after an action, run a test that should FAIL if the
attack is contained (e.g. connectivity to an isolated host should time out).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, List


@dataclass
class VerificationResult:
    scenario: str
    contained: bool
    details: str = ""


class Verifier:
    def __init__(self):
        self._checks: List[tuple[str, Callable[[], bool]]] = []

    def register(self, name: str, check: Callable[[], bool]) -> None:
        """Register a probe. `check` returns True when the threat is contained."""
        self._checks.append((name, check))

    def run(self, scenario: str) -> VerificationResult:
        """Run all registered checks; contained only if all pass."""
        if not self._checks:
            return VerificationResult(scenario, False, "No containment probes configured")
        failures = []
        for name, check in self._checks:
            try:
                if not check():
                    failures.append(name)
            except Exception as exc:  # noqa: BLE001 - report probe errors
                failures.append(f"{name} (error: {exc})")

        if failures:
            return VerificationResult(scenario, False, "; ".join(failures))
        return VerificationResult(scenario, True, "all probes passed")
