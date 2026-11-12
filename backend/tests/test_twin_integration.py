import uuid
import pytest
from app.core.config import settings
from app.models.pipeline import PipelineJob
from app.services import detection, twin
from test_unified_pipeline import ingest
from acdt.evaluation.harness import EvaluationReport, TrialResult


class RecordingGraph:
    def __init__(self):
        self.calls = []
        self.closed = False
    def bootstrap(self):
        self.calls.append(('bootstrap', {}))
    def upsert_host(self, hostname, **props):
        self.calls.append(('host', {'hostname':hostname, **props}))
    def upsert_connection(self, src, dst):
        self.calls.append(('connection', {'src':src,'dst':dst}))
    def run(self, query, **params):
        self.calls.append((query, params))
        return []
    def close(self):
        self.closed = True


def test_event_projects_host_and_network_into_same_twin(client, db_setup, monkeypatch):
    monkeypatch.setattr(settings, 'NEO4J_ENABLED', True)
    event_id = ingest(client, 'wazuh', {'rule':{'id':'100','level':8}, 'agent':{'id':'001','name':'web-01','ip':'10.0.0.10'}, 'data':{'srcip':'10.0.0.10','dstip':'10.0.0.20'}})
    detection.evaluate_and_alert.run(str(event_id))
    graph = RecordingGraph()
    monkeypatch.setattr(twin, 'graph_client', lambda:graph)
    detection.project_event.run(str(event_id))
    detection.project_event.run(str(event_id))
    assert graph.closed
    assert sum(kind == 'bootstrap' for kind, _ in graph.calls) == 1
    assert any(kind == 'host' and props['hostname'] == 'web-01' for kind, props in graph.calls)
    assert any(kind == 'connection' and props['src'] == '10.0.0.10' for kind, props in graph.calls)
    assert any(props.get('event_id') == str(event_id) for _, props in graph.calls)
    with db_setup() as db:
        job = db.get(PipelineJob,event_id)
        assert job.status == 'processed' and job.twin_status == 'synced'


def test_graph_outage_does_not_undo_detection(client, db_setup, monkeypatch):
    monkeypatch.setattr(settings,'NEO4J_ENABLED',True)
    event_id = ingest(client,'falco',{'rule':'Shell','hostname':'web-01'})
    detection.evaluate_and_alert.run(str(event_id))
    def fail(db,event):
        raise ConnectionError('graph unavailable')
    monkeypatch.setattr(twin,'project_to_twin',fail)
    with pytest.raises(ConnectionError):
        detection.project_event.run(str(event_id))
    with db_setup() as db:
        job = db.get(PipelineJob,event_id)
        assert job.status == 'processed' and job.twin_status == 'failed'
        assert job.twin_attempts == 1


def test_zero_duration_trials_are_included_in_metrics():
    report = EvaluationReport([TrialResult('instant', True, 0), TrialResult('later',True,2)])
    assert report.mttd == 1
