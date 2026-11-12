import uuid
import pytest
from app.core.config import settings
from app.core.security import create_access_token
from app.services import twin


@pytest.mark.parametrize("path", ["/defense/status", "/defense/actions", "/twin", "/twin/paths?from_host=web-01"])
def test_defense_reads_require_authentication(client, path):
    assert client.get(f"/api/v1{path}").status_code == 401


def test_defense_mutation_requires_admin(client):
    headers = {"Authorization": f"Bearer {create_access_token({'sub':'analyst'})}"}
    response = client.post(f"/api/v1/defense/incidents/{uuid.uuid4()}/plan", headers=headers, json={})
    assert response.status_code == 403


def test_disabled_twin_and_real_processing_counts(client, auth_headers):
    assert client.get("/api/v1/twin", headers=auth_headers).json()["backend"] == "local-simulation"
    result = client.get("/api/v1/defense/status", headers=auth_headers).json()
    assert result["execution_mode"] == "simulation"
    assert result["processing"] == {}
    assert len(result["policies"]) == 4


def test_overview_exposes_empty_dataset_counts_without_fabricated_metrics(client, auth_headers):
    response = client.get("/api/v1/defense/overview", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert {name: data[name] for name in ["total_events", "total_alerts", "total_incidents", "simulated_actions"]} == {
        "total_events": 0, "total_alerts": 0, "total_incidents": 0, "simulated_actions": 0,
    }
    assert "accuracy" not in data and "containment_rate" not in data


def test_twin_outage_is_reported(client, auth_headers, monkeypatch):
    monkeypatch.setattr(settings, "NEO4J_ENABLED", True)
    def fail():
        raise ConnectionError("neo4j unavailable")
    monkeypatch.setattr(twin, "twin_snapshot", fail)
    assert client.get("/api/v1/twin", headers=auth_headers).status_code == 503


def test_acdt_risk_model_is_exposed_with_validation(client, auth_headers):
    response = client.post("/api/v1/defense/risk", headers=auth_headers, json={"edge_probabilities":[0.5,0.5], "asset_value":100})
    assert response.json()["risk"] == 25
    response = client.post("/api/v1/defense/risk", headers=auth_headers, json={"edge_probabilities":[1.2], "asset_value":100})
    assert response.status_code == 422
