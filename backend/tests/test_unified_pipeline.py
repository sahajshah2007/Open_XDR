import json
import uuid
from pathlib import Path
import pytest
from app.models.event import Event
from app.models.alert import Alert
from app.models.host import Host
from app.models.incident import Incident
from app.models.pipeline import PipelineJob, ResponseAction, IntegrationSetting
from app.services import detection
from app.services.configuration import read_setting

INGEST_HEADERS = {"x-api-key": "test-ingest-key"}
ROOT = Path(__file__).resolve().parents[2]


def ingest(client, source, data):
    response = client.post("/api/v1/ingest/events", headers=INGEST_HEADERS, json={"source": source, "data": data})
    assert response.status_code == 202, response.text
    return uuid.UUID(response.json()["event_id"])


def test_wazuh_fixture_to_persistent_incident_and_idempotent_worker(client, db_setup):
    event_id = ingest(client, "wazuh", json.loads((ROOT / "integrations/wazuh/sample_alerts.json").read_text()))
    detection.evaluate_and_alert.run(str(event_id))
    detection.evaluate_and_alert.run(str(event_id))
    with db_setup() as db:
        assert db.query(Event).count() == 1
        assert db.query(Alert).count() == 1
        assert db.query(Incident).count() == 1
        alert = db.query(Alert).one()
        assert alert.rule_id == "wazuh:5716"
        assert alert.mitre_technique == "T1110"
        assert alert.mitre_tactic == "credential-access"
        assert db.get(PipelineJob, event_id).status == "processed"
        assert db.query(Host).one().host_name == "ubuntu-lab-01"


def test_suricata_fixture_is_native_alert(client, db_setup):
    event_id = ingest(client, "suricata", json.loads((ROOT / "integrations/suricata/sample_alerts.json").read_text()))
    detection.evaluate_and_alert.run(str(event_id))
    with db_setup() as db:
        assert db.query(Alert).one().rule_id == "suricata:2010935"


def test_zeek_connection_is_telemetry_without_invented_detection(client, db_setup):
    event_id = ingest(client, "zeek", json.loads((ROOT / "integrations/zeek/sample_conn.json").read_text()))
    detection.evaluate_and_alert.run(str(event_id))
    with db_setup() as db:
        assert db.query(Alert).count() == 0
        assert db.get(Event, event_id).normalized["timestamp"].endswith("Z") or "+00:00" in db.get(Event, event_id).normalized["timestamp"]


def test_falco_to_policy_plan_and_audited_simulation(client, db_setup, auth_headers):
    event_id = ingest(client, "falco", {"rule":"Web shell", "hostname":"web-01", "priority":"Critical", "tags":["T1505.003"], "time":"2026-11-04T12:00:00Z"})
    detection.evaluate_and_alert.run(str(event_id))
    with db_setup() as db:
        incident_id = db.query(Incident).one().incident_id
    response = client.post(f"/api/v1/defense/incidents/{incident_id}/plan", headers=auth_headers, json={})
    assert response.status_code == 200, response.text
    actions = response.json()
    assert len(actions) == 1 and actions[0]["policy_id"] == "web_shell"
    action_id = actions[0]["action_id"]
    simulated = client.post(f"/api/v1/defense/actions/{action_id}/simulate", headers=auth_headers)
    assert simulated.status_code == 200
    assert simulated.json()["status"] == "simulated"
    assert simulated.json()["result"]["contained"] is False
    overview = client.get("/api/v1/defense/overview", headers=auth_headers).json()
    assert overview["total_events"] == 1
    assert overview["total_alerts"] == 1
    assert overview["total_incidents"] == 1
    assert overview["simulated_actions"] == 1
    client.post(f"/api/v1/defense/incidents/{incident_id}/plan", headers=auth_headers, json={})
    repeated = client.post(f"/api/v1/defense/actions/{action_id}/simulate", headers=auth_headers)
    assert repeated.json()["executed_at"] == simulated.json()["executed_at"]
    with db_setup() as db:
        assert db.query(ResponseAction).count() == 1


def test_broker_outage_keeps_durable_processing_intent(client, db_setup, monkeypatch):
    def fail(**kwargs):
        raise ConnectionError("broker unavailable")
    monkeypatch.setattr(detection.evaluate_and_alert, "apply_async", fail)
    event_id = ingest(client, "falco", {"rule":"Shell", "hostname":"web-01"})
    with db_setup() as db:
        assert db.get(Event, event_id) is not None
        assert db.get(PipelineJob, event_id).status == "pending"


def test_failed_processing_rolls_back_and_can_be_retried(client, db_setup, monkeypatch):
    event_id = ingest(client, "falco", {"rule":"Shell", "hostname":"web-01"})
    original = detection.rule_engine.match_event
    def fail(event):
        raise ValueError("invalid detection")
    monkeypatch.setattr(detection.rule_engine, "match_event", fail)
    with pytest.raises(ValueError):
        detection.evaluate_and_alert.run(str(event_id))
    with db_setup() as db:
        job = db.get(PipelineJob, event_id)
        assert job.status == "failed" and job.attempts == 1
        assert db.query(Alert).count() == 0
    monkeypatch.setattr(detection.rule_engine, "match_event", original)
    detection.evaluate_and_alert.run(str(event_id))
    with db_setup() as db:
        assert db.get(PipelineJob, event_id).status == "processed"
        assert db.query(Alert).count() == 1


def test_unknown_source_and_bad_timestamp_are_rejected(client, db_setup):
    for source, data in [("unknown", {}), ("wazuh", {"timestamp":"not-a-time"})]:
        response = client.post("/api/v1/ingest/events", headers=INGEST_HEADERS, json={"source":source, "data":data})
        assert response.status_code == 422
    with db_setup() as db:
        assert db.query(Event).count() == 0


def test_settings_are_encrypted_and_shared_between_sessions(client, db_setup, auth_headers):
    response = client.post("/api/v1/settings/otx-key", headers=auth_headers, json={"otx_api_key":"example-test-key"})
    assert response.status_code == 200
    with db_setup() as db:
        assert "example-test-key" not in db.get(IntegrationSetting, "otx_api_key").encrypted_value
        assert read_setting(db, "otx_api_key") == "example-test-key"


def test_nullable_assignment_can_be_cleared(client, db_setup, auth_headers):
    event_id = ingest(client, "falco", {"rule":"Shell", "hostname":"web-01"})
    detection.evaluate_and_alert.run(str(event_id))
    with db_setup() as db:
        incident_id = db.query(Incident).one().incident_id
    client.patch(f"/api/v1/incidents/{incident_id}", headers=auth_headers, json={"assignee_id":"analyst-id"})
    response = client.patch(f"/api/v1/incidents/{incident_id}", headers=auth_headers, json={"assignee_id":None})
    assert response.json()["assignee_id"] is None


def test_wazuh_and_falco_share_asset_and_incident(client, db_setup):
    first = ingest(client, 'wazuh', {'timestamp':'2026-11-04T12:00:00Z', 'rule':{'id':'100','level':8}, 'agent':{'id':'001','name':'web-01'}})
    second = ingest(client, 'falco', {'time':'2026-11-04T12:01:00Z', 'rule':'Web shell', 'hostname':'web-01', 'tags':['T1505.003']})
    detection.evaluate_and_alert.run(str(first))
    detection.evaluate_and_alert.run(str(second))
    with db_setup() as db:
        assert db.query(Host).count() == 1
        assert db.query(Incident).count() == 1
        assert db.query(Alert).count() == 2
        assert len({alert.host_id for alert in db.query(Alert).all()}) == 1
        assert 'T1505.003' in db.query(Incident).one().mitre_techniques
