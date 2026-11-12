"""Thin Neo4j client wrapper for the Digital Twin."""
from __future__ import annotations

from typing import Any, Optional

from acdt.config import settings
from acdt.graph import schema


class GraphClient:
    """Wraps the Neo4j driver with helpers for twin updates and queries."""

    def __init__(self, uri: Optional[str] = None, user: Optional[str] = None,
                 password: Optional[str] = None):
        self._uri = uri or settings.NEO4J_URI
        self._user = user or settings.NEO4J_USER
        self._password = password or settings.NEO4J_PASSWORD
        self._driver = None

    def connect(self):
        """Lazily create the Neo4j driver (imported here to keep deps optional)."""
        if self._driver is None:
            from neo4j import GraphDatabase
            self._driver = GraphDatabase.driver(
                self._uri, auth=(self._user, self._password),
                connection_timeout=3, max_transaction_retry_time=3
            )
        return self._driver

    def close(self):
        if self._driver is not None:
            self._driver.close()
            self._driver = None

    def run(self, cypher: str, **params) -> list[dict[str, Any]]:
        """Execute a Cypher statement and return records as dicts."""
        driver = self.connect()
        with driver.session() as session:
            result = session.run(cypher, **params)
            return [record.data() for record in result]

    def bootstrap(self) -> None:
        """Apply schema constraints and indexes."""
        for stmt in schema.bootstrap_statements():
            self.run(stmt)

    # --- twin mutation helpers -------------------------------------------

    def upsert_host(self, hostname: str, **props) -> None:
        self.run(
            "MERGE (h:Host {hostname: $hostname}) SET h += $props",
            hostname=hostname, props=props,
        )

    def upsert_connection(self, src_ip: str, dst_ip: str) -> None:
        """Record observed network connectivity between two hosts."""
        self.run(
            "OPTIONAL MATCH (known_a:Host {ip: $src}) "
            "WITH coalesce(known_a.hostname, $src) AS src_name "
            "MERGE (a:Host {hostname: src_name}) SET a.ip = $src "
            "WITH a OPTIONAL MATCH (known_b:Host {ip: $dst}) "
            "WITH a, coalesce(known_b.hostname, $dst) AS dst_name "
            "MERGE (b:Host {hostname: dst_name}) SET b.ip = $dst "
            "MERGE (a)-[:CONNECTS_TO]->(b)",
            src=src_ip, dst=dst_ip,
        )

    def mark_isolated(self, hostname: str, isolated: bool = True) -> None:
        self.run(
            "MATCH (h:Host {hostname: $hostname}) SET h.is_isolated = $isolated",
            hostname=hostname, isolated=isolated,
        )
