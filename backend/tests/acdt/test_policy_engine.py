from acdt.policy_engine.engine import PolicyEngine
from app.core.config import settings


def test_policy_matches_technique_and_risk():
    engine = PolicyEngine(settings.POLICY_FILE)
    decisions = engine.evaluate({
        "attack_techniques": ["T1550"],
        "risk_score": 0.9,
        "user": "alice",
        "target_host": "db-01",
    })
    ids = [d.policy_id for d in decisions]
    assert "high_privilege_escalation" in ids

    decision = next(d for d in decisions if d.policy_id == "high_privilege_escalation")
    assert decision.autonomy == "auto"
    # %user% should be interpolated.
    assert any("alice" in a for a in decision.actions)


def test_policy_no_match_below_threshold():
    engine = PolicyEngine(settings.POLICY_FILE)
    decisions = engine.evaluate({
        "attack_techniques": ["T1550"],
        "risk_score": 0.1,
    })
    assert "high_privilege_escalation" not in [d.policy_id for d in decisions]
