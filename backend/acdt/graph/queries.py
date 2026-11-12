"""Reusable Cypher queries for attack-path discovery and analysis."""

# Shortest path from a compromised host to a critical data asset.
SHORTEST_PATH_TO_CRITICAL = """
MATCH (src:Host {hostname: $start})
MATCH (target:DataAsset {critical: true})
MATCH p = shortestPath((src)-[:CONNECTS_TO|HOSTS|USES*1..10]->(target))
RETURN [n IN nodes(p) | coalesce(n.hostname, n.id, n.name)] AS nodes, length(p) AS hops
LIMIT 50
"""

# Hosts reachable through a compromised identity's privileges.
PRIV_ESCALATION_REACH = """
MATCH (u:Identity {username: $username})-[:HAS_PRIVILEGE|RUNS_AS*1..3]->(h:Host)
RETURN DISTINCT h.hostname AS hostname
"""

# All paths up to N hops between two hosts (rank client-side by risk).
# NOTE: Neo4j does not allow a parameter inside a variable-length bound
# (`[*1..$max_hops]`), so max_hops is injected via str.format by the caller
# using paths_between(). Keep max_hops an int from a trusted source only.
PATHS_BETWEEN_TEMPLATE = """
MATCH (src:Host {{hostname: $start}}), (tgt:Host {{hostname: $target}})
MATCH p = (src)-[*1..{max_hops}]->(tgt)
RETURN p
LIMIT $limit
"""


def paths_between(max_hops: int = 5) -> str:
    """Build the PATHS_BETWEEN query with a fixed hop bound."""
    return PATHS_BETWEEN_TEMPLATE.format(max_hops=int(max_hops))
