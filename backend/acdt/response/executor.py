"""Route policy actions to the correct adapter and log outcomes."""
from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict

from acdt.response.adapters import (
    CloudMockAdapter,
    DockerAdapter,
    IptablesAdapter,
    KubernetesAdapter,
)

logger = logging.getLogger("acdt.response.executor")

# Parses "ActionName(key=value, key2=value2)".
_ACTION_RE = re.compile(r"(\w+)\((.*)\)")


@dataclass
class ActionResult:
    action: str
    target: str
    result: str
    details: str = ""

    def to_json(self) -> str:
        return json.dumps({
            "time": datetime.now(tz=timezone.utc).isoformat(),
            "action": self.action,
            "target": self.target,
            "result": self.result,
            "details": self.details,
        })


class ResponseExecutor:
    """Maps action verbs to adapters and executes them safely."""

    def __init__(self):
        self.docker = DockerAdapter()
        self.iptables = IptablesAdapter()
        self.k8s = KubernetesAdapter()
        self.cloud = CloudMockAdapter()

        # action verb -> (adapter, adapter action)
        self._routes = {
            "IsolateHost": (self.iptables, "drop"),
            "BlockPort": (self.iptables, "drop_port"),
            "KillContainer": (self.docker, "kill"),
            "RevokeCredentials": (self.cloud, "revoke"),
            "CordonNode": (self.k8s, "cordon"),
        }

    def perform(self, action_str: str) -> ActionResult:
        """Parse and execute a single action string like 'IsolateHost(host=web-01)'."""
        verb, params = self._parse(action_str)
        route = self._routes.get(verb)
        if route is None:
            return ActionResult(verb, str(params), "failed", "unknown action")

        adapter, adapter_action = route
        ok = adapter.execute(adapter_action, **params)
        result = ActionResult(
            verb,
            params.get("host") or params.get("container") or params.get("user", ""),
            "simulated" if ok else "failed",
            "Simulation only; no infrastructure was changed" if ok else "Simulation failed",
        )
        logger.info(result.to_json())
        return result

    def _parse(self, action_str: str) -> tuple[str, Dict[str, str]]:
        match = _ACTION_RE.match(action_str.strip())
        if not match:
            return action_str, {}
        verb, arg_str = match.groups()
        params: Dict[str, str] = {}
        for pair in filter(None, (p.strip() for p in arg_str.split(","))):
            if "=" in pair:
                k, v = pair.split("=", 1)
                params[k.strip()] = v.strip()
        return verb, params
