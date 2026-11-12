import uuid
from datetime import datetime,timezone
import pytest
from app.models.experiment import ExperimentEvent,ExperimentRun,EventAlert
from app.models.event import Event
from app.models.alert import Alert
from app.models.incident import Incident
from app.services.detection import evaluate_and_alert
from app.services.experiments import finalize_experiment,evaluate_evidence
from app.services.scenarios import build_scenario,SCENARIOS


def complete(client,db_setup,auth_headers,scenario,seed=42):
    response=client.post('/api/v1/experiments/runs',headers=auth_headers,json={'scenario_id':scenario,'seed':seed})
    assert response.status_code==202,response.text
    run_id=response.json()['run_id']
    with db_setup() as db:
        ids=[str(row.event_id) for row in db.query(ExperimentEvent).filter_by(run_id=uuid.UUID(run_id)).order_by(ExperimentEvent.position)]
    for event_id in ids: evaluate_and_alert.run(event_id)
    finalize_experiment.run(run_id)
    result=client.get(f'/api/v1/experiments/runs/{run_id}',headers=auth_headers)
    assert result.status_code==200,result.text
    return result.json()


@pytest.mark.parametrize('scenario',[item['id'] for item in SCENARIOS])
def test_all_scenarios_replay_evaluate_and_report(client,db_setup,auth_headers,scenario):
    result=complete(client,db_setup,auth_headers,scenario)
    assert result['status']=='completed',result
    assert result['simulation_only'] is True
    assert result['events_processed']==result['events_total']
    assert result['metrics']['events']==len(result['events'])
    assert {row['stage'] for row in result['traces']} >= {'source','normalize','queue','detect','correlate','twin','policy','verify','evaluate'}
    assert result['verification']['real_containment_performed'] is False
    if scenario in ['ssh-bruteforce','web-shell','lateral-movement','credential-reuse']:
        assert result['metrics']['tp']>0
        assert result['verification']['simulated_containment'] is True,result['verification']
    if scenario=='dns-detection-gap':
        assert result['metrics']['fn']==1
        assert result['metrics']['recall']==0
        assert result['metrics']['precision'] is None
        assert result['metrics']['coverage'][0]['status']=='missed'
    if scenario=='noisy-sensor':
        assert result['metrics']['fp']==1
        assert result['metrics']['precision']==0
    if scenario=='benign-maintenance':
        assert result['metrics']['tn']==3
        assert result['metrics']['precision'] is None
    for format in ['html','json','csv']:
        report=client.get(f"/api/v1/experiments/runs/{result['run_id']}/report?format={format}",headers=auth_headers)
        assert report.status_code==200,report.text
        assert 'attachment' in report.headers['content-disposition']
        if format=='html': assert 'No real attacks or containment commands' in report.text
        if format=='json': assert report.json()['run_id']==result['run_id']
        if format=='csv': assert 'expected_alert' in report.text


def test_replay_isolated_from_prior_runs_and_idempotent(client,db_setup,auth_headers):
    first=complete(client,db_setup,auth_headers,'web-shell')
    second=complete(client,db_setup,auth_headers,'web-shell')
    first_cases={item['incident_id'] for event in first['events'] for item in event['alerts']}
    second_cases={item['incident_id'] for event in second['events'] for item in event['alerts']}
    assert first_cases.isdisjoint(second_cases)
    assert first['seed']==second['seed']
    assert first['metrics']['tp']==second['metrics']['tp']
    with db_setup() as db: count=db.query(Alert).count()
    finalize_experiment.run(first['run_id'])
    for event in first['events']: evaluate_and_alert.run(event['event_id'])
    with db_setup() as db: assert db.query(Alert).count()==count


def test_fixture_seed_is_reproducible_and_no_commands_execute():
    identifier=uuid.uuid4();start=datetime(2026,11,5,tzinfo=timezone.utc)
    assert build_scenario('ssh-bruteforce',42,identifier,start)==build_scenario('ssh-bruteforce',42,identifier,start)
    assert build_scenario('ssh-bruteforce',43,identifier,start)!=build_scenario('ssh-bruteforce',42,identifier,start)


def test_experiment_permissions_and_reserved_metadata(client,auth_headers):
    assert client.get('/api/v1/experiments/scenarios').status_code==401
    assert client.post('/api/v1/experiments/runs',json={'scenario_id':'web-shell'}).status_code==401
    assert client.post('/api/v1/experiments/runs',headers=auth_headers,json={'scenario_id':'not-a-scenario'}).status_code==422
    assert client.post('/api/v1/experiments/runs',headers=auth_headers,json={'scenario_id':'web-shell','seed':-1}).status_code==422
    assert client.post('/api/v1/ingest/events',headers={'x-api-key':'test-ingest-key'},json={'source':'falco','data':{'_lab':{'run_id':'spoofed'}}}).status_code==422


def test_pending_reports_and_experiment_admin_boundary(client,auth_headers):
    from app.core.security import create_access_token
    run=client.post('/api/v1/experiments/runs',headers=auth_headers,json={'scenario_id':'web-shell'}).json()
    assert client.get(f"/api/v1/experiments/runs/{run['run_id']}/report",headers=auth_headers).status_code==409
    analyst={'Authorization':f"Bearer {create_access_token({'sub':'analyst'})}"}
    assert client.get('/api/v1/experiments/scenarios',headers=analyst).status_code==200
    assert client.post('/api/v1/experiments/runs',headers=analyst,json={'scenario_id':'web-shell'}).status_code==403
    assert client.post(f"/api/v1/experiments/runs/{run['run_id']}/retry",headers=analyst).status_code==403


def test_recorded_local_twin_keeps_reused_fixture_addresses_separate(client,db_setup,auth_headers):
    from app.services.twin import local_snapshot,local_paths
    first=complete(client,db_setup,auth_headers,'lateral-movement')
    second=complete(client,db_setup,auth_headers,'lateral-movement')
    with db_setup() as db:
        graph=local_snapshot(db)
        by_name={node['name']:node['id'] for node in graph['nodes']}
        edges={(edge['source'],edge['target']) for edge in graph['edges']}
        origins=[];destinations=[]
        for run in [first,second]:
            nodes={node['id']:node for node in run['topology']['nodes']}
            # The web source is only observed as an address; no endpoint fixture
            # reports its identity, so the graph must not invent a named host.
            source=next(node for node in graph['nodes'] if node['ip']==nodes['web']['ip'] and run['run_id'] in node['id'])
            target=by_name[nodes['db']['name']]
            assert (source['id'],target) in edges
            assert local_paths(db,source['name'])==[{'nodes':[source['name'],nodes['db']['name']],'hops':1}]
            origins.append(source['id']);destinations.append(target)
        assert origins[0]!=origins[1]
        assert (origins[0],destinations[1]) not in edges
