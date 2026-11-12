"""Action adapters for Docker, iptables, Kubernetes, and mock cloud.

These adapters log simulation intent and return without modifying infrastructure.
They do not implement real containment, state checks, or external SDK calls.
"""
from __future__ import annotations

import logging
from typing import Protocol

logger = logging.getLogger("acdt.response")


class Adapter(Protocol):
    def execute(self, action: str, **params) -> bool: ...


class DockerAdapter:
    """Record a simulated container action without invoking Docker."""

    def execute(self, action: str, **params) -> bool:
        container = params.get("container")
        # Deliberately simulation-only: log intent without external side effects.
        logger.info("DockerAdapter %s container=%s", action, container)
        return True


class IptablesAdapter:
    """Record simulated traffic isolation without modifying firewall rules."""

    def execute(self, action: str, **params) -> bool:
        ip = params.get("ip") or params.get("host")
        # Deliberately simulation-only: log intent without external side effects.
        logger.info("IptablesAdapter %s ip=%s", action, ip)
        return True


class KubernetesAdapter:
    """Record a simulated orchestration action without invoking Kubernetes."""

    def execute(self, action: str, **params) -> bool:
        target = params.get("pod") or params.get("node")
        # Deliberately simulation-only: log intent without external side effects.
        logger.info("KubernetesAdapter %s target=%s", action, target)
        return True


class CloudMockAdapter:
    """Record a simulated identity action without contacting an IAM service."""

    def execute(self, action: str, **params) -> bool:
        user = params.get("user")
        # Deliberately simulation-only: log intent without external side effects.
        logger.info("CloudMockAdapter %s user=%s", action, user)
        return True
