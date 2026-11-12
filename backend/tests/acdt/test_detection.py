from acdt.detection.attack_map import techniques_for
from acdt.detection.correlator import Correlator
from acdt.telemetry.normalizer import normalize


def test_techniques_from_falco_tags():
    ev = normalize("falco", {
        "rule": "Terminal shell in container",
        "tags": ["container", "T1059"],
        "time": "2023-05-25T13:44:05Z",
    })
    assert "T1059" in techniques_for(ev)


def test_techniques_from_lookup():
    ev = normalize("attacker", {
        "time": "2023-09-01T12:35:10Z",
        "action": "brute_force",
        "target": "web-01",
    })
    assert "T1110" in techniques_for(ev)


def test_correlator_groups_by_entity():
    corr = Correlator(window_seconds=60)
    ev = normalize("attacker", {
        "time": "2023-09-01T12:35:10Z",
        "action": "brute_force",
        "target": "web-01",
    })
    incident = corr.ingest(ev)
    assert "T1110" in incident.techniques
    assert 0.0 < incident.confidence <= 1.0
