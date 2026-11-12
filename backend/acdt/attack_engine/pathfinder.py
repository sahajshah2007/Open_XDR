"""Discover and rank attack paths on the Digital Twin."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from acdt.attack_engine import risk
from acdt.graph import queries
from acdt.graph.client import GraphClient


@dataclass
class AttackPath:
    nodes: List[str]
    edge_probs: List[float]
    asset_value: float = 1.0

    @property
    def probability(self) -> float:
        return risk.path_probability(self.edge_probs)

    @property
    def risk(self) -> float:
        return risk.risk_score(self.edge_probs, self.asset_value)


class AttackEngine:
    """Runs graph queries to enumerate attack paths and score them."""

    def __init__(self, client: Optional[GraphClient] = None):
        self.client = client or GraphClient()

    def shortest_path_to_critical(self, start_host: str) -> List[dict]:
        """Find the shortest path from a host to any critical data asset."""
        return self.client.run(
            queries.SHORTEST_PATH_TO_CRITICAL, start=start_host
        )

    def privilege_reach(self, username: str) -> List[str]:
        """Hosts reachable via a compromised identity's privileges."""
        rows = self.client.run(queries.PRIV_ESCALATION_REACH, username=username)
        return [r["hostname"] for r in rows]

    def rank_paths(self, paths: List[AttackPath]) -> List[AttackPath]:
        """Rank candidate attack paths by descending risk score."""
        return sorted(paths, key=lambda p: p.risk, reverse=True)
