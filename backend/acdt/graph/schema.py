"""Digital Twin schema: node labels, relationship types, and constraints.

Node labels:
    Host, Container, Service, Application, Database, DataAsset,
    Identity, Vulnerability, AttackStep, Network

Relationship types:
    RUNS_AS, HOSTS, EXPOSES_PORT, CONNECTS_TO, CONTAINS, USES,
    HAS_PRIVILEGE, CONNECTED_TO, VULNERABLE_TO, CAN_ACCESS, ATTACK
"""

NODE_LABELS = [
    "Host", "Container", "Service", "Application", "Database",
    "DataAsset", "Identity", "Vulnerability", "AttackStep", "Network",
]

RELATIONSHIP_TYPES = [
    "RUNS_AS", "HOSTS", "EXPOSES_PORT", "CONNECTS_TO", "CONTAINS", "USES",
    "HAS_PRIVILEGE", "CONNECTED_TO", "VULNERABLE_TO", "CAN_ACCESS", "ATTACK",
]

# Constraints / indexes to apply on startup.
CONSTRAINTS = [
    "CREATE CONSTRAINT host_hostname IF NOT EXISTS "
    "FOR (h:Host) REQUIRE h.hostname IS UNIQUE",
    "CREATE CONSTRAINT identity_username IF NOT EXISTS "
    "FOR (i:Identity) REQUIRE i.username IS UNIQUE",
    "CREATE CONSTRAINT vuln_cve IF NOT EXISTS "
    "FOR (v:Vulnerability) REQUIRE v.cve IS UNIQUE",
]

INDEXES = [
    "CREATE INDEX host_ip IF NOT EXISTS FOR (h:Host) ON (h.ip)",
    "CREATE INDEX service_name IF NOT EXISTS FOR (s:Service) ON (s.name)",
]


def bootstrap_statements():
    """Return the list of Cypher statements to initialize the schema."""
    return CONSTRAINTS + INDEXES
