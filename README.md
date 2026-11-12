# TwinTrace Lab — Cyber Defense Simulation

An educational portfolio project for studying how endpoint and network evidence
becomes an explainable investigation and a simulated defense decision.

Use **recorded or synthetic telemetry** to explore event normalization, ATT&CK
metadata, incident correlation, local digital twins, and response-policy
simulations. Response adapters only record dry runs: they do not isolate hosts,
change firewalls, kill containers, or revoke real credentials.

The web UI includes a seven-scenario **New experiment** workspace, animated **Flow
studio**, event-level evaluation and exportable reports, and a six-chapter
**Interview guide** with figures, an illustrative photo, and presentation mode.
Investigations, original evidence, asset context, Twin & response, and a Project
notebook remain available.

See the [portfolio and demonstration guide](docs/portfolio.md). OpenXDR and ACDT
are the original source projects; their [comparison and merge notes](docs/merge.md)
remain available for provenance. Existing database and Docker volume names are
retained so changing the project identity does not replace the dataset.

## Run the simulation lab

Requires Docker with Compose. Preserve your existing `.env` when upgrading.
For a fresh checkout, copy `.env.example` to `.env`, then replace the JWT secret,
admin password and ingest key. Generate random secrets with:

```sh
python3 -c 'import secrets; print(secrets.token_urlsafe(32))'
```

```sh
docker compose up --build -d
```

- Dashboard: http://localhost:5173
- API documentation: http://localhost:8000/docs
- Login: `ADMIN_USERNAME` and `ADMIN_PASSWORD` from `.env`
- Reproducible experiments: **New experiment** (`/experiments`)
- Detection experiments: **Compare runs** (`/compare`)
- Animated processing chain: **Flow studio** (`/flow`)
- Interview presentation: **Interview guide** (`/guide`)
- Policy exploration: **Twin & response**
- Implementation map and résumé notes: **Project notebook**

The API migrates the database before accepting traffic. A worker evaluates events;
a scheduler recovers pending jobs every ten seconds. Existing PostgreSQL data is
retained in the same Compose volume. Keep the existing database password when
reusing that volume; setting a new environment value does not rotate its password.
No previously running ACDT database is imported automatically.

The PostgreSQL URL explicitly selects the installed `psycopg2` driver. Older
`postgresql://` and `postgres://` URLs in existing `.env` files are normalized
automatically. Databases carrying the legacy migration marker `95faffc550e2`
upgrade through a compatibility revision before adding the unified-platform tables.

## Run a reproducible experiment

Open **New experiment**, select a scenario, set a seed and optional name, then
choose **Run simulation**. The fixtures are JSON data; no attack commands run.

Available scenarios: SSH brute force, web shell, lateral movement, credential
reuse, benign maintenance, a DNS detection gap, and a noisy-sensor false positive.
Each run stores its fixture version, unique ID, isolated asset identities,
independent truth labels, source/normalized records, and processing traces.
The seed repeats logical content; timestamps and run-specific identities change.
**Replay same seed** creates another run. **New experiment** returns to the catalog
without deleting prior evidence or existing investigations.

The API commits synthetic events and durable processing intent, then dispatches
through Redis/Celery. Finalization compares actual event-linked alerts against
fixture labels and evaluates YAML policies against resulting incidents. Responses
update only the run-local topology; assertions verify modeled state. The scheduler
also recovers pending experiment finalization every three seconds.

- **Animated flow:** pause, step, scrub, or change the speed of recorded traces.
  Playback is explanatory and time-compressed, not live packet traffic.
- **Evidence:** inspect independent labels, observed alerts and original records.
- **Evaluation:** event-level TP/FP/FN/TN, precision, recall, F1, and processing latency.
  Missing denominators appear as N/A. Latency spans durable ingestion through
  processing completion for true positives, excluding virtual fixture timestamps.
- **ATT&CK coverage:** compare expected and observed exact technique IDs separately
  from event-level classification. A source alert alone is not proof of detection
  efficacy. The deliberate DNS miss and noisy-sensor FP demonstrate that distinction.
- **Digital twin:** view modeled isolation, blocked ports, revoked identities and
  state assertions. `real_containment_performed` always remains false.
- **Report:** download a standalone HTML report (print to PDF), complete JSON, or
  event evidence CSV. Reports contain only that run's synthetic evidence.

These small synthetic fixtures demonstrate measurement and pipeline behavior;
their metrics are not estimates of production security performance. Fixtures,
labels and technique mappings live in `backend/app/services/scenarios.py`.

Authenticated API endpoints are under `/api/v1/experiments`; creating and retrying
runs requires the configured administrator. The `_lab` raw field is reserved for
this internal runner and rejected on the external ingest endpoint.

## Compare detection experiments

Open **Compare runs** (`/compare`) to launch two runs of the same scenario and seed
with different detection configurations, or select existing completed runs.

- **Baseline** preserves the current default behavior (native Wazuh level ≥ 3).
- **DNS fixture coverage** adds an optional Sigma rule for the synthetic encoded
  DNS pattern. It demonstrates turning the documented DNS miss into a linked alert;
  it is a teaching signature for this fixture, not a validated DNS-tunneling detector.
- **Higher Wazuh threshold** accepts native Wazuh alerts at level ≥ 12. It suppresses
  the noisy-sensor example but also misses the lower-level SSH alerts. Independently
  matching Sigma rules still run.

The configuration editor can select native-alert sources, set the Wazuh threshold,
and enable catalog rules. **Save configuration** creates an immutable database
record; editing starts a new copy. Experiment runs save full rule bodies, settings,
and a SHA-256 fingerprint in their own snapshots. Workers and retries read that
snapshot, so rule reloads or changed files cannot alter a queued run's configuration.
New-run replay preserves these detector inputs. Legacy runs remain readable and
are labeled as lacking captured rule settings; their UI replay starts a fresh baseline.
Normal external ingest continues to use the global rule settings.

Comparisons show event classifications and rule matches, precision/recall/F1 and
count deltas, ATT&CK changes, model outcomes, and saved configurations. Deltas are
candidate minus baseline, with ratio changes in percentage points. N/A remains
undefined rather than becoming zero. Deltas are withheld if scenario, seed, fixture
version, ordering, or independent truth labels differ. Matching tiny fixtures do
not control queue load, application-code changes, or response-policy versions.

Download the comparison as standalone printable HTML or JSON. Comparison URLs
retain both run IDs for later demonstrations. `/api/v1/experiments/configurations`
provides configurations; `/compare/runs`, `/compare`, and `/compare/report` under
that same experiments prefix implement creation, comparison and export.

### Digital twin and optional Neo4j

The default local twin derives connectivity from stored evidence; experiment runs
also have their own scenario topology. Both work without a graph service.

For an additional Neo4j projection, set `NEO4J_ENABLED=true` and a strong `NEO4J_PASSWORD` in `.env`, then run:

```sh
docker compose --profile twin up --build -d
```

Neo4j Browser is at http://localhost:7474. The API uses the private Bolt connection.
Ingest new telemetry to populate the graph. Hosts with criticality 8–10 project as
critical assets. Changes to host criticality appear in Neo4j after subsequent
telemetry from that host. Earlier graph-disabled events remain unprojected.

The graph shows **observed connectivity**, not verified exploitable attack paths.
Neo4j is optional: detection and incident workflows continue when it is unavailable.

## Ingest telemetry

Sensors run outside this application. Forward each JSON event to the shared API:

```sh
curl http://localhost:8000/api/v1/ingest/events \
  -H 'Content-Type: application/json' \
  -H 'x-api-key: YOUR_INGEST_API_KEY' \
  -d '{"source":"falco","data":{"hostname":"web-01","rule":"Web shell","priority":"Critical","tags":["T1505.003"]}}'
```

Supported sources: `wazuh`, `suricata`, `zeek`, `falco`, and `attacker` (lab signals).
Wazuh, Suricata and Falco alerts retain their upstream detections. Ordinary Zeek
connections are stored and projected without automatically being declared attacks.
Invalid timestamps and unknown sources return 422.

The API returns 202 after storing both the event and its processing record. Redis
outages leave durable pending work for the scheduler. Processing and twin failures
are recorded separately, with up to five automatic attempts. An administrator can
reset failed work through `POST /api/v1/defense/events/{event_id}/retry`.

## Detection and response

- `rules/local/` is the default enabled Sigma collection. The previous SigmaHQ
  archive remains under `rules/sigmahq/`; set `RULES_DIR` explicitly to evaluate a
  selected collection. The evaluator implements a conservative subset and rejects
  unsupported syntax. Rule count is not a measure of verified detection coverage.
  After cloning, fetch the optional archive with
  `git submodule update --init --recursive`.
- OTX enrichment is optional. Keys saved in Settings are encrypted in PostgreSQL
  and read by workers. Preserve `JWT_SECRET`: it also derives the settings
  encryption key, so rotating it requires re-saving integration keys.
- `backend/config/policies.yaml` contains ACDT's response policies. In **Twin &
  response**, choose an incident, evaluate policies, then simulate a proposal.
  Policies requiring a user can be evaluated through the API with `{"user":"alice"}`.
- **All response adapters are simulations.** The platform records proposals and
  attempts but does not isolate hosts, revoke real credentials or claim successful
  containment. Policy autonomy is retained as experiment metadata; real response
  adapters are outside this portfolio project’s scope.
- `POST /api/v1/defense/risk` exposes ACDT's what-if path model using supplied edge
  probabilities and asset value; estimates assume independent probabilities.

## Local development and verification

Python 3.11+ and Node 22 are recommended for the merged runtime. Start PostgreSQL
and Redis separately and set `DATABASE_URL` and `REDIS_URL` to their reachable
addresses. The Compose services are intentionally not published to the host.

```sh
python3.11 -m venv backend/.venv
backend/.venv/bin/pip install -r backend/requirements-dev.txt
cd backend
.venv/bin/uvicorn app.main:app --reload
```

In another terminal, from the project root:

```sh
npm --prefix frontend ci
npm --prefix frontend run dev
```

Vite proxies `/api` and WebSocket requests to localhost:8000. The container build
serves the compiled frontend through Nginx with the same API paths.

```sh
backend/.venv/bin/python -m pytest backend/tests -q
npm --prefix frontend run lint
npm --prefix frontend run build
```

Tests use isolated SQLite databases and mocked broker/graph boundaries. Live deployment checks should exercise PostgreSQL/Redis/Celery separately from
the isolated test suite. Neo4j remains an optional integration boundary.

## Layout

- `backend/app/`: unified API, storage, ingestion, detection and incident processing
- `backend/acdt/`: imported twin, attack analysis, policy, response and evaluation modules
- `backend/config/`: response policies
- `frontend/`: scenario runner, animated flow, interview guide and investigation UI
- `rules/`: enabled local rules and retained SigmaHQ archive
- `integrations/`: example source events
- `lab/acdt/`: optional isolated ACDT laboratory, excluded from normal deployment
- `docs/`: comparison, integration notes and original design specifications
