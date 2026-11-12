from acdt.attack_engine.risk import (
    combined_or,
    cvss_to_probability,
    path_probability,
    risk_score,
)
from acdt.response.executor import ResponseExecutor


def test_cvss_to_probability_clamped():
    assert round(cvss_to_probability(9.8), 2) == 0.98
    assert cvss_to_probability(20) == 1.0
    assert cvss_to_probability(-1) == 0.0


def test_path_probability_and_risk():
    assert path_probability([0.4, 0.2, 0.3]) == 0.4 * 0.2 * 0.3
    assert risk_score([0.5, 0.5], 100) == 25.0


def test_combined_or():
    assert round(combined_or([0.8, 0.8]), 2) == 0.96


def test_executor_parses_and_routes():
    executor = ResponseExecutor()
    result = executor.perform("IsolateHost(host=web-01)")
    assert result.action == "IsolateHost"
    assert result.target == "web-01"
    assert result.result == "simulated"


def test_executor_unknown_action():
    executor = ResponseExecutor()
    result = executor.perform("Nonexistent(x=1)")
    assert result.result == "failed"
