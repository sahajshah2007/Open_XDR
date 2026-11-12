from acdt.telemetry.normalizer import normalize


def test_normalize_zeek():
    event = {
        "ts": 1591367999.305988,
        "id.orig_h": "192.168.4.76",
        "id.resp_h": "192.168.4.1",
        "proto": "udp",
        "service": "dns",
    }
    ev = normalize("zeek", event)
    assert ev.source == "zeek"
    assert ev.src_ip == "192.168.4.76"
    assert ev.dst_ip == "192.168.4.1"
    assert ev.event_type == "dns"


def test_normalize_falco():
    event = {
        "rule": "Terminal shell in container",
        "priority": "Critical",
        "tags": ["container", "T1059", "shell"],
        "time": "2023-05-25T13:44:05.478Z",
    }
    ev = normalize("falco", event)
    assert ev.source == "falco"
    assert ev.event_type == "Terminal shell in container"


def test_normalize_attacker():
    event = {
        "time": "2023-09-01T12:35:10Z",
        "attacker_ip": "172.17.0.10",
        "action": "brute_force",
        "target": "web-01",
    }
    ev = normalize("attacker", event)
    assert ev.source == "attacker"
    assert ev.event_type == "brute_force"
    assert ev.dst_ip == "web-01"
