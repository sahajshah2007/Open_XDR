"""Evaluate policies against incidents and emit action decisions."""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import yaml

from acdt.config import settings

_CONTAINS_RE = re.compile(r"attack_techniques\s+contains\s+(\S+)")
_COMPARE_RE = re.compile(r"(\w+)\s*(>|>=|<|<=|==)\s*([\d.]+)")


@dataclass
class Policy:
    id: str
    description: str
    when: List[str]
    actions: List[str]
    autonomy: str  # auto | require_approval | manual


@dataclass
class Decision:
    policy_id: str
    actions: List[str]
    autonomy: str


class PolicyEngine:
    def __init__(self, policy_file: Optional[str] = None):
        self.policies: List[Policy] = []
        self.load(policy_file or settings.POLICY_FILE)

    def load(self, path: str) -> None:
        with open(path, "r") as fh:
            data = yaml.safe_load(fh) or {}
        self.policies = [
            Policy(
                id=p["id"],
                description=p.get("description", ""),
                when=p.get("when", []),
                actions=p.get("actions", []),
                autonomy=p.get("autonomy", "manual"),
            )
            for p in data.get("policies", [])
        ]

    def evaluate(self, context: Dict[str, Any]) -> List[Decision]:
        """Return decisions for every policy whose conditions all match."""
        decisions = []
        for policy in self.policies:
            if all(self._match(cond, context) for cond in policy.when):
                actions = [self._interpolate(a, context) for a in policy.actions]
                decisions.append(
                    Decision(policy.id, actions, policy.autonomy)
                )
        return decisions

    def _match(self, condition: str, context: Dict[str, Any]) -> bool:
        contains = _CONTAINS_RE.search(condition)
        if contains:
            technique = contains.group(1)
            techniques = context.get("attack_techniques", [])
            return any(t.startswith(technique) for t in techniques)

        compare = _COMPARE_RE.search(condition)
        if compare:
            field, op, value = compare.groups()
            actual = float(context.get(field, 0))
            expected = float(value)
            return {
                ">": actual > expected,
                ">=": actual >= expected,
                "<": actual < expected,
                "<=": actual <= expected,
                "==": actual == expected,
            }[op]
        return False

    def _interpolate(self, action: str, context: Dict[str, Any]) -> str:
        """Replace %var% placeholders with values from the context."""
        def repl(match):
            return str(context.get(match.group(1), match.group(0)))

        return re.sub(r"%(\w+)%", repl, action)
