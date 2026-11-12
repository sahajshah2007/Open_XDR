import copy
import uuid
import pytest
from app.core.security import create_access_token
from app.models.experiment import ExperimentEvent, ExperimentRun, DetectionProfile
from app.services.detection import evaluate_and_alert
from app.services.experiments import finalize_experiment
from app.services import detection_profiles

BASE = '/api/v1/experiments'


def process(db_setup, run_id):
    with db_setup() as db:
        events = [str(row.event_id) for row in db.query(ExperimentEvent).filter_by(run_id=uuid.UUID(run_id)).order_by(ExperimentEvent.position)]
    for event_id in events:
        evaluate_and_alert.run(event_id)
    finalize_experiment.run(run_id)


def run(client, db_setup, auth_headers, scenario, profile='baseline', seed=42):
    response = client.post(BASE + '/runs', headers=auth_headers, json={'scenario_id': scenario, 'seed': seed, 'profile_id': profile})
    assert response.status_code == 202, response.text
    identifier = response.json()['run_id']
    process(db_setup, identifier)
    return client.get(BASE + '/runs/' + identifier, headers=auth_headers).json()


def compare(client, headers, left, right):
    return client.get(BASE + '/compare', headers=headers, params={'baseline': left['run_id'], 'candidate': right['run_id']})


def test_configuration_catalog_and_immutable_saved_snapshot(client, db_setup, auth_headers):
    catalog = client.get(BASE + '/configurations', headers=auth_headers).json()
    assert len(catalog['profiles']) == 3
    assert any(row['id'] == 'twintrace-dns-fixture-v1' for row in catalog['rules'])
    response = client.post(BASE + '/configurations', headers=auth_headers, json={
        'name': 'My DNS configuration', 'description': 'Reviewed teaching fixture',
        'native_sources': ['wazuh', 'falco'], 'wazuh_min_level': 12,
        'rule_ids': ['twintrace-dns-fixture-v1'],
    })
    assert response.status_code == 201, response.text
    saved = response.json()
    assert saved['builtin'] is False
    assert saved['snapshot']['sigma_rules'][0]['detection']['selection']['raw.query|startswith'] == 'encoded-lab-sample.'
    assert len(saved['fingerprint']) == 64
    assert client.patch(BASE + '/configurations/' + saved['profile_id'], headers=auth_headers, json={'name': 'Overwrite'}).status_code == 404
    with db_setup() as db:
        assert db.query(DetectionProfile).count() == 1
        assert db.get(DetectionProfile, uuid.UUID(saved['profile_id'])).snapshot == saved['snapshot']


def test_pinned_rules_survive_catalog_changes_before_worker_delivery(client, db_setup, auth_headers, monkeypatch):
    saved = client.post(BASE + '/configurations', headers=auth_headers, json={
        'name': 'Pinned DNS', 'native_sources': [], 'rule_ids': ['twintrace-dns-fixture-v1'],
    }).json()
    response = client.post(BASE + '/runs', headers=auth_headers, json={'scenario_id': 'dns-detection-gap', 'profile_id': saved['profile_id']})
    identifier = response.json()['run_id']
    # No rules remain on disk/in the catalog when the task actually runs.
    monkeypatch.setattr(detection_profiles, 'rule_catalog', lambda: ({}, []))
    process(db_setup, identifier)
    detail = client.get(BASE + '/runs/' + identifier, headers=auth_headers).json()
    assert detail['metrics']['tp'] == 1
    assert detail['metrics']['fn'] == 0
    assert detail['detection_config']['fingerprint'] == saved['fingerprint']
    replay = client.post(BASE + '/runs', headers=auth_headers, json={'scenario_id': 'dns-detection-gap', 'seed': 42, 'replay_of': identifier}).json()
    process(db_setup, replay['run_id'])
    result = client.get(BASE + '/runs/' + replay['run_id'], headers=auth_headers).json()
    assert result['metrics']['tp'] == 1
    assert result['detection_config']['fingerprint'] == saved['fingerprint']


def test_paired_dns_rule_experiment_uses_real_event_links(client, db_setup, auth_headers):
    response = client.post(BASE + '/compare/runs', headers=auth_headers, json={'scenario_id': 'dns-detection-gap'})
    assert response.status_code == 202, response.text
    pair = response.json()
    for item in pair.values():
        process(db_setup, item['run_id'])
    result = compare(client, auth_headers, pair['baseline'], pair['candidate'])
    assert result.status_code == 200, result.text
    data = result.json()
    assert data['comparable'] is True
    assert data['metric_deltas']['tp'] == 1
    assert data['metric_deltas']['fn'] == -1
    assert data['metric_deltas']['precision'] is None
    assert data['metric_deltas']['recall'] == 1
    assert data['summary']['improved'] == 1
    assert data['summary']['regressed'] == 0
    assert data['configuration_changes']['added_rules'] == ['twintrace-dns-fixture-v1']
    assert data['coverage_changes'][0]['baseline_status'] == 'missed'
    assert data['coverage_changes'][0]['candidate_status'] == 'detected'
    assert data['event_changes'][0]['baseline_class'] == 'fn'
    assert data['event_changes'][0]['candidate_class'] == 'tp'
    assert data['candidate']['verification']['real_containment_performed'] is False
    for format in ['json', 'html']:
        report = client.get(BASE + '/compare/report', headers=auth_headers, params={'baseline': pair['baseline']['run_id'], 'candidate': pair['candidate']['run_id'], 'format': format})
        assert report.status_code == 200, report.text
        assert 'attachment' in report.headers['content-disposition']
        if format == 'html':
            assert 'Synthetic encoded DNS fixture' in report.text
            assert 'Real containment performed: false' in report.text


@pytest.mark.parametrize('scenario,field,change,outcome', [
    ('noisy-sensor', 'fp', -1, 'improved'),
    ('ssh-bruteforce', 'fn', 3, 'regressed'),
])
def test_threshold_experiment_exposes_benefit_and_regression(client, db_setup, auth_headers, scenario, field, change, outcome):
    left = run(client, db_setup, auth_headers, scenario)
    right = run(client, db_setup, auth_headers, scenario, 'high-threshold')
    result = compare(client, auth_headers, left, right).json()
    assert result['metric_deltas'][field] == change
    assert result['summary'][outcome] > 0
    if scenario == 'ssh-bruteforce':
        web = next(node for node in result['model_changes'] if node['asset'] == 'web')
        assert web['baseline_ports'] == [22]
        assert web['candidate_ports'] == []
        assert web['changed'] is True
    assert result['configuration_changes']['wazuh_threshold_change'] == 9


@pytest.mark.parametrize('scenario,seed,reason', [('dns-detection-gap', 43, 'different seeds'), ('noisy-sensor', 42, 'different scenarios')])
def test_nonmatching_fixtures_do_not_produce_misleading_deltas(client, db_setup, auth_headers, scenario, seed, reason):
    left = run(client, db_setup, auth_headers, 'dns-detection-gap')
    right = run(client, db_setup, auth_headers, scenario, seed=seed)
    data = compare(client, auth_headers, left, right).json()
    assert data['comparable'] is False
    assert any(reason in item for item in data['reasons'])
    assert data['metric_deltas'] == {}
    assert data['event_changes'] == []


def test_legacy_configuration_is_unknown_and_history_is_unchanged(client, db_setup, auth_headers):
    left = run(client, db_setup, auth_headers, 'dns-detection-gap')
    right = run(client, db_setup, auth_headers, 'dns-detection-gap', 'dns-coverage')
    with db_setup.begin() as db:
        previous = db.get(ExperimentRun, uuid.UUID(left['run_id']))
        snapshot = copy.deepcopy(previous.snapshot)
        snapshot.pop('detection_config')
        previous.snapshot = snapshot
        original_metrics = copy.deepcopy(previous.metrics)
    result = compare(client, auth_headers, left, right).json()
    assert result['warnings']
    assert result['configuration_changes']['known'] is False
    with db_setup() as db:
        assert db.get(ExperimentRun, uuid.UUID(left['run_id'])).metrics == original_metrics


def test_profile_validation_permissions_and_pair_atomicity(client, db_setup, auth_headers):
    analyst = {'Authorization': f"Bearer {create_access_token({'sub':'analyst'})}"}
    assert client.get(BASE + '/configurations').status_code == 401
    assert client.get(BASE + '/compare', params={'baseline': uuid.uuid4(), 'candidate': uuid.uuid4()}).status_code == 401
    assert client.get(BASE + '/configurations', headers=analyst).status_code == 200
    assert client.post(BASE + '/configurations', headers=analyst, json={'name': 'Forbidden'}).status_code == 403
    assert client.post(BASE + '/compare/runs', headers=analyst, json={'scenario_id': 'web-shell'}).status_code == 403
    for payload in [{'name': ' '}, {'name': 'Bad', 'wazuh_min_level': 16}, {'name': 'Bad', 'native_sources': ['unknown']}, {'name': 'Bad', 'rule_ids': ['missing']}, {'name': 'Bad', 'sigma_rules': []}]:
        assert client.post(BASE + '/configurations', headers=auth_headers, json=payload).status_code == 422
    with db_setup() as db:
        before = db.query(ExperimentRun).count()
    response = client.post(BASE + '/compare/runs', headers=auth_headers, json={'scenario_id': 'web-shell', 'candidate_profile_id': 'missing'})
    assert response.status_code == 422
    with db_setup() as db:
        assert db.query(ExperimentRun).count() == before


def test_pending_same_run_and_replay_validation(client, db_setup, auth_headers):
    pair = client.post(BASE + '/compare/runs', headers=auth_headers, json={'scenario_id': 'dns-detection-gap'}).json()
    assert compare(client, auth_headers, pair['baseline'], pair['candidate']).status_code == 409
    assert compare(client, auth_headers, pair['baseline'], pair['baseline']).status_code == 422
    response = client.post(BASE + '/runs', headers=auth_headers, json={'scenario_id': 'dns-detection-gap', 'seed': 43, 'replay_of': pair['baseline']['run_id']})
    assert response.status_code == 422
    with db_setup.begin() as db:
        db.get(ExperimentRun, uuid.UUID(pair['candidate']['run_id'])).status = 'failed'
    failed = compare(client, auth_headers, pair['baseline'], pair['candidate'])
    assert failed.status_code == 409
    assert failed.json()['detail']['state'] == 'failed'


def test_saved_profiles_do_not_change_external_ingest(client, db_setup, auth_headers):
    experiment = run(client, db_setup, auth_headers, 'dns-detection-gap', 'dns-coverage')
    raw = copy.deepcopy(experiment['events'][0]['raw'])
    raw.pop('_lab')
    response = client.post('/api/v1/ingest/events', headers={'x-api-key': 'test-ingest-key'}, json={'source': 'zeek', 'data': raw})
    assert response.status_code == 202
    evaluate_and_alert.run(response.json()['event_id'])
    from app.models.experiment import EventAlert
    with db_setup() as db:
        assert db.query(EventAlert).filter_by(event_id=uuid.UUID(response.json()['event_id'])).count() == 0


def test_changed_ground_truth_with_matching_seed_is_not_aligned(client, db_setup, auth_headers):
    left = run(client, db_setup, auth_headers, 'dns-detection-gap')
    right = run(client, db_setup, auth_headers, 'dns-detection-gap', 'dns-coverage')
    with db_setup.begin() as db:
        expected = db.query(ExperimentEvent).filter_by(run_id=uuid.UUID(right['run_id']), position=0).one()
        expected.label = 'A different reviewed observation'
    result = compare(client, auth_headers, left, right).json()
    assert result['comparable'] is False
    assert result['metric_deltas'] == {}
    assert any('truth labels' in message for message in result['reasons'])
