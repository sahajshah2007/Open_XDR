"""A standalone, escaped comparison report from persisted evaluation results."""
import json
from html import escape


def html_comparison(data):
    def e(value):
        return escape(str(value))
    def value(number):
        return 'N/A' if number is None else e(number)
    metrics = ''.join(f'<tr><td>{e(key)}</td><td>{value(data["baseline"]["metrics"].get(key))}</td><td>{value(data["candidate"]["metrics"].get(key))}</td><td>{value(delta)}</td></tr>' for key, delta in data['metric_deltas'].items())
    events = ''.join(f'<tr><td>{e(row["label"])}</td><td>{e(row["baseline_class"].upper())}</td><td>{e(row["candidate_class"].upper())}</td><td>{e(row["outcome"])}</td></tr>' for row in data['event_changes'])
    coverage = ''.join(f'<tr><td>{e(row["technique"])}</td><td>{e(row["name"])}</td><td>{e(row["baseline_status"])}</td><td>{e(row["candidate_status"])}</td></tr>' for row in data['coverage_changes'])
    profiles = ''.join(f'<h3>{label}: {e(data[side]["name"])}</h3><p>Run: {e(data[side]["run_id"])} · Seed {data[side]["seed"]}</p><pre>{e(json.dumps(data[side]["configuration_snapshot"], indent=2))}</pre>' for label, side in [('Baseline', 'baseline'), ('Candidate', 'candidate')])
    notices = ''.join(f'<p>{e(note)}</p>' for note in data['reasons'] + data['warnings'])
    return f'''<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>TwinTrace Lab — Experiment comparison</title><style>body{{font:14px/1.7 system-ui;color:#203044;max-width:1050px;margin:35px auto;padding:0 24px}}table{{border-collapse:collapse;width:100%;font-size:12px}}th,td{{border-bottom:1px solid #dce2e8;padding:10px;text-align:left}}h2{{margin-top:32px}}pre{{white-space:pre-wrap;overflow-wrap:anywhere;font-size:11px;background:#f4f6f8;padding:18px}}.scope{{padding:14px;background:#fbf6eb;border-left:4px solid #ba9558}}@media print{{body{{margin:0}}h2{{break-after:avoid}}tr{{break-inside:avoid}}}}</style></head><body><p>TWINTRACE LAB / SAVED EXPERIMENT COMPARISON</p><h1>Measure what changed.</h1><p class="scope">Simulation only. Real containment performed: false.</p><p>Comparable fixtures: {e(data['comparable'])}. Improved events: {data['summary']['improved']}. Regressed events: {data['summary']['regressed']}.</p>{notices}<p>{e(data['methodology'])}</p><h2>Candidate minus baseline</h2><p>Ratios are shown as fractions; latency is milliseconds. N/A means an undefined denominator or an unavailable comparison.</p><table><tr><th>Metric</th><th>Baseline</th><th>Candidate</th><th>Delta</th></tr>{metrics}</table><h2>Event changes</h2><table><tr><th>Observation</th><th>Baseline</th><th>Candidate</th><th>Outcome</th></tr>{events}</table><h2>ATT&amp;CK changes</h2><table><tr><th>ID</th><th>Technique</th><th>Baseline</th><th>Candidate</th></tr>{coverage}</table><h2>Configuration changes</h2><pre>{e(json.dumps(data['configuration_changes'], indent=2))}</pre><h2>Simulated model changes</h2><pre>{e(json.dumps(data['model_changes'], indent=2))}</pre><h2>Saved detector inputs</h2>{profiles}<p>Save this HTML file or print it to PDF. The JSON comparison includes the complete machine-readable results.</p></body></html>'''
