# TwinTrace Lab — portfolio guide

## Positioning

**Cyber Defense Simulation Lab** is the project's scope. It demonstrates how
recorded or synthetic endpoint and network evidence can be normalized, correlated,
explored as an optional graph, and used to study a simulated response decision.

The backend, storage, worker pipeline, authentication, and UI are implemented.
The input evidence belongs to a controlled lab dataset. The response adapters log
intent and record `simulated` outcomes; they do not change real infrastructure.

## Résumé wording

**TwinTrace Lab | Python, FastAPI, React, TypeScript, PostgreSQL, Redis/Celery, Neo4j, Docker**

- Built a cyber-defense simulation workbench that normalizes Wazuh, Suricata,
  Zeek, and Falco telemetry into persistent, ATT&CK-mapped investigations.
- Integrated an optional Neo4j connectivity twin and YAML response policies with
  an auditable simulation journal and an interactive investigation interface.
- Built seeded, isolated scenario replay with animated processing traces, labeled
  evaluation, ATT&CK coverage and exportable experiment reports.
- Added durable event-processing records, retry recovery, idempotent task handling,
  database migrations, and regression coverage for detection and failure paths.

Adjust the wording to the parts you can personally explain and demonstrate. Do not
claim production deployment, real attack prevention, autonomous containment,
accuracy percentages, or measured detection latency without supporting evidence.

## A short interview walkthrough

1. **Interview guide:** open `/guide`, choose **Present project**, and explain the
   purpose and architecture figure. The lab photo is explicitly an AI-generated
   illustration, not evidence of a physical deployment.
2. **New experiment:** replay SSH brute force with seed 42. Explain how durable
   event storage and Redis/Celery delivery produce a saved run.
3. **Animated flow and Evidence:** pause a stage, inspect its JSON, then compare
   an original source event with its normalized record and linked alerts.
4. **Evaluation and ATT&CK coverage:** show actual run metrics and expected versus
   observed techniques. Repeat with DNS detection gap and noisy sensor to show
   false negatives and false positives rather than claiming universal detection.
5. **Digital twin and Report:** show modeled port blocking or isolation, its state
   assertions, and download HTML (printable to PDF), JSON or CSV evidence.
6. **Replay same seed:** show another run ID and preserved history. Return to the
   guide's final chapter for engineering tradeoffs and the timed demo script.

Flow studio (`/flow`) also provides a clearly labeled illustrative walkthrough
without creating stored evidence, and can play an actual saved run's journal.
Use arrow keys between interview chapters; Escape exits presentation mode.
The Project notebook retains a copyable summary and static downloadable brief.

## Completed simulation experiments

Seven versioned scenarios are implemented: SSH brute force, web shell, lateral
movement, credential reuse, benign maintenance, DNS detection gap, and noisy
sensor. Each stores a seed, run ID, independent fixture labels, source records,
actual event-linked alerts, processing traces, coverage and reports. Replays use
the shared ingestion/parsing and asynchronous worker path. New runs preserve old
runs and existing imported records.

Evaluation classifies each event by whether an alert was expected and whether any
alert was actually linked to it. Precision = TP/(TP+FP), recall = TP/(TP+FN), and
F1 is their harmonic mean when the denominators are defined. Exact-ID technique
coverage is separate. Mean latency measures durable ingestion to processing
completion for true positives, including queue delay. Virtual fixture timestamps
are not latency clocks. Undefined quantities appear as N/A.

Policies update only a run-local model, then verify isolation, port blocking or
credential revocation against that model. No-action runs do not infer containment.
The actual system is a simulation: fixture metrics describe these tiny labeled
examples, not operational effectiveness against unknown attacks.

## Detection engineering walkthrough (v0.4)

Open **Compare runs** and launch DNS detection gap with Baseline versus DNS fixture
coverage. Show the same seed and matching truth labels, the FN → TP event change,
missed → detected technique, and exact added rule. Undefined baseline precision
remains N/A, so its precision delta is not reported as a fabricated improvement.

Next, compare the higher Wazuh threshold against Baseline on noisy sensor and SSH
brute force. Explain why filtering an alert can reduce noise while creating misses.
Inspect the changed simulated port-blocking outcome. Save a named configuration,
use it in another experiment, and inspect its saved rule bodies and fingerprint.
Export HTML/JSON to keep an auditable demonstration result.

Each run pins detector inputs. Legacy runs have unknown original settings and are
labeled accordingly. Application code and response policies are not version-pinned;
queue load affects measured latency. Keep these limits explicit in interview claims.

## Sensible future extensions

Add larger reviewed datasets, a custom scenario builder, multi-seed batch analysis,
and tests against an explicitly enabled live Neo4j service. These are
extensions beyond the completed replay, evaluation and presentation workflow.

## Demonstration boundaries

- Existing records may predate the new lab interface; the rename does not relabel
  their raw source data or fabricate a replay history.
- Neo4j is optional. Network reachability alone does not prove an exploitable path.
- Confidence/priority and path-risk formulas are heuristics, not validated probabilities.
- The enabled rule evaluator supports a conservative Sigma subset.
- No response adapter executes firewall, Docker, Kubernetes, or cloud IAM changes.
