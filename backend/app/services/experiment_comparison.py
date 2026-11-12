"""Compare saved, independently evaluated runs without recalculating history."""
from app.services.experiments import run_detail
from app.services.detection_profiles import canonical

METRICS = ['tp', 'fp', 'fn', 'tn', 'precision', 'recall', 'f1', 'accuracy', 'coverage_ratio', 'mean_detection_ms']


def fixture_signature(detail):
    return [(row['position'], row['source'], row['label'], row['expected_positive'], sorted(row['expected_techniques'])) for row in detail['events']]


def config_diff(left, right):
    if not left or not right:
        return {'known': False, 'added_rules': [], 'removed_rules': [], 'changed_rules': [],
                'added_native_sources': [], 'removed_native_sources': [], 'wazuh_threshold_change': None}
    a = {str(rule['id']): rule for rule in left['sigma_rules']}
    b = {str(rule['id']): rule for rule in right['sigma_rules']}
    return {
        'known': True, 'same_fingerprint': left['fingerprint'] == right['fingerprint'],
        'added_rules': sorted(b.keys() - a.keys()), 'removed_rules': sorted(a.keys() - b.keys()),
        'changed_rules': sorted(key for key in a.keys() & b.keys() if canonical(a[key]) != canonical(b[key])),
        'added_native_sources': sorted(set(right['native_sources']) - set(left['native_sources'])),
        'removed_native_sources': sorted(set(left['native_sources']) - set(right['native_sources'])),
        'wazuh_threshold_change': right['wazuh_min_level'] - left['wazuh_min_level'],
    }


def compare_runs(db, baseline, candidate):
    left, right = run_detail(db, baseline), run_detail(db, candidate)
    reasons = []
    if left['scenario_id'] != right['scenario_id']:
        reasons.append('The runs use different scenarios.')
    if left['seed'] != right['seed']:
        reasons.append('The runs use different seeds.')
    if left['snapshot']['version'] != right['snapshot']['version']:
        reasons.append('The runs use different fixture versions.')
    if fixture_signature(left) != fixture_signature(right):
        reasons.append('Event ordering or independent truth labels do not match.')
    comparable = not reasons
    warnings = []
    if not left['detection_config'] or not right['detection_config']:
        warnings.append('A legacy run has no saved detection configuration. Its original rule settings cannot be reconstructed.')
    differences = {}
    if comparable:
        for key in METRICS:
            a, b = left['metrics'].get(key), right['metrics'].get(key)
            differences[key] = round(b - a, 6) if a is not None and b is not None else None
    changes = []
    if comparable:
        for a, b in zip(left['events'], right['events']):
            a_rules = sorted({alert['rule_id'] for alert in a['alerts']})
            b_rules = sorted({alert['rule_id'] for alert in b['alerts']})
            was_correct, now_correct = a['classification'] in {'tp', 'tn'}, b['classification'] in {'tp', 'tn'}
            outcome = 'improved' if now_correct and not was_correct else 'regressed' if was_correct and not now_correct else 'unchanged'
            changed = a['classification'] != b['classification'] or a_rules != b_rules or a['observed_techniques'] != b['observed_techniques']
            changes.append({'position': a['position'], 'label': a['label'], 'source': a['source'],
                            'expected_positive': a['expected_positive'], 'baseline_class': a['classification'],
                            'candidate_class': b['classification'], 'baseline_rules': a_rules, 'candidate_rules': b_rules,
                            'added_techniques': sorted(set(b['observed_techniques']) - set(a['observed_techniques'])),
                            'removed_techniques': sorted(set(a['observed_techniques']) - set(b['observed_techniques'])),
                            'changed': changed, 'outcome': outcome})
    a_coverage = {item['technique']: item for item in left['metrics']['coverage']}
    b_coverage = {item['technique']: item for item in right['metrics']['coverage']}
    coverage = [{**(b_coverage.get(key) or a_coverage[key]),
                 'baseline_status': a_coverage.get(key, {}).get('status', 'not-exercised'),
                 'candidate_status': b_coverage.get(key, {}).get('status', 'not-exercised')}
                for key in sorted(a_coverage.keys() | b_coverage.keys())] if comparable else []
    a_nodes = {node['id']: node for node in left['topology']['nodes']}
    b_nodes = {node['id']: node for node in right['topology']['nodes']}
    models = []
    if comparable:
        for key in a_nodes.keys() & b_nodes.keys():
            a, b = a_nodes[key], b_nodes[key]
            models.append({'asset': key, 'baseline_name': a['name'], 'candidate_name': b['name'],
                           'baseline_state': a['state'], 'candidate_state': b['state'],
                           'baseline_ports': a['blocked_ports'], 'candidate_ports': b['blocked_ports'],
                           'changed': (a['state'], a['blocked_ports']) != (b['state'], b['blocked_ports'])})
    def run_view(detail):
        return {key: detail[key] for key in ['run_id', 'scenario_id', 'name', 'seed', 'status', 'created_at',
                                            'metrics', 'detection_config', 'verification']} | {
            'configuration_snapshot': detail['snapshot'].get('detection_config'),
        }
    return {
        'baseline': run_view(left), 'candidate': run_view(right), 'comparable': comparable,
        'reasons': reasons, 'warnings': warnings, 'metric_deltas': differences,
        'configuration_changes': config_diff(left['snapshot'].get('detection_config'), right['snapshot'].get('detection_config')),
        'event_changes': changes, 'coverage_changes': coverage,
        'model_changes': sorted(models, key=lambda node: node['asset']),
        'summary': {'improved': sum(row['outcome'] == 'improved' for row in changes),
                    'regressed': sum(row['outcome'] == 'regressed' for row in changes),
                    'changed': sum(row['changed'] for row in changes)},
        'methodology': 'Deltas are candidate minus baseline. Events align by fixture position only when scenario, seed, version, ordering and truth labels match. Rule bodies and native-alert settings are pinned for new runs. Latency also depends on queue load; response policies and application code are not version-pinned. These are small synthetic-fixture comparisons, not production benchmarks.',
        'simulation_only': True,
    }
