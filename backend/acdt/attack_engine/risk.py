"""Risk scoring for attack paths.

Model:
    - Each edge carries an exploit probability `p` in [0, 1]
      (e.g. derived from CVSS/10 or privilege type).
    - Path probability = product of edge probabilities.
    - Final risk = path_probability * asset_value.
"""
from __future__ import annotations

from typing import Iterable


def cvss_to_probability(cvss: float) -> float:
    """Map a CVSS score (0-10) to an exploit probability (0-1)."""
    return max(0.0, min(cvss / 10.0, 1.0))


def path_probability(edge_probs: Iterable[float]) -> float:
    """Combine independent edge probabilities into a path probability."""
    prob = 1.0
    for p in edge_probs:
        prob *= p
    return prob


def combined_or(probs: Iterable[float]) -> float:
    """Probabilistic OR: 1 - product(1 - p). Used for alternative paths."""
    complement = 1.0
    for p in probs:
        complement *= (1.0 - p)
    return 1.0 - complement


def risk_score(edge_probs: Iterable[float], asset_value: float) -> float:
    """Final risk = path probability * asset value."""
    return path_probability(edge_probs) * asset_value
