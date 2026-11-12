> Historical design reference: the current project is TwinTrace Lab, an educational cyber defense simulation. Real infrastructure response and production deployment proposals in this original blueprint are outside the current project scope.

# OpenXDR: Open-Source EDR/XDR Platform Blueprint

## 1. Project Summary

This project replaces the custom endpoint agent with proven open-source telemetry sources and focuses on the higher-value layers: detection engineering, correlation, threat intelligence, incident reconstruction, and response workflows.

The core idea is to build a **mini XDR platform** on top of existing security tools such as Wazuh, Suricata, Zeek, and Sigma. Instead of reinventing endpoint collection, the platform ingests alerts and logs from trusted sources and adds a custom intelligence layer that makes the system stand out as a portfolio project.

### Main goals

- Use open-source telemetry sources instead of building a new EDR agent from scratch.
- Normalize data from endpoint, network, and threat-intelligence sources.
- Correlate related events into incidents, not just alerts.
- Add attack-story reconstruction, risk scoring, and investigator-friendly timelines.
- Provide a modern dashboard for triage, hunting, and reporting.
- Keep the system realistic for a homelab or small lab cluster.

---

## 2. Product Positioning

### What this is

A **security operations platform** that sits above open-source EDR/XDR and SIEM-like tools.

### What this is not

- Not a commercial EDR replacement.
- Not a pure log viewer.
- Not a basic Wazuh deployment with a nicer UI.

### Why this is unique

Most open-source security setups stop at alert collection. This project goes further by adding:

- cross-source correlation,
- incident grouping,
- risk-based alerting,
- ATT&CK coverage analytics,
- investigation summaries,
- optional AI-assisted triage,
- response actions and playbooks.

This makes it closer to a lightweight XDR platform than a simple SIEM dashboard.

---

## 3. Suggested Open-Source Stack

### Telemetry sources

- **Wazuh** for host telemetry, agent-based endpoint visibility, file integrity monitoring, log collection, and security alerts.
- **Suricata** for IDS/IPS network alerts.
- **Zeek** for rich network metadata such as DNS, HTTP, SSL/TLS, and connection logs.
- **Sigma** rules for normalized detection logic.
- **MITRE ATT&CK** mappings for tactic and technique context.
- **VirusTotal** or **AbuseIPDB** for external enrichment.
- Optional: **MISP** for IOC feeds and threat intelligence correlation.

### Custom platform components

- **FastAPI backend** for API and orchestration.
- **Redis** for queueing, caching, and fast correlation state.
- **PostgreSQL** for durable storage and analytics.
- **React dashboard** for investigation and operations.
- Optional **Celery/RQ/async workers** for background jobs.

---

## 4. High-Level Architecture

```text
Endpoints / Hosts
   ├── Wazuh Agent
   └── Local Logs / Security Telemetry

Network Sensors
   ├── Suricata
   └── Zeek

Threat Intel
   ├── AbuseIPDB
   ├── VirusTotal
   └── MISP

            ↓

      Ingestion Layer
      ├── FastAPI
      └── Normalization Service

            ↓

     Detection & Correlation
     ├── Sigma Rule Engine
     ├── Event Correlator
     ├── Risk Scoring
     └── Suppression / Deduplication

            ↓

     Storage & Enrichment
     ├── PostgreSQL
     ├── Redis Cache
     └── Enrichment Workers

            ↓

     Investigation & Response
     ├── Incident Timeline
     ├── ATT&CK Heatmap
     ├── Search / Hunting
     ├── Alerts Dashboard
     └── Response Playbooks
```

---

## 5. Core Design Principles

### 5.1 Use existing collection where possible

Endpoint collection is expensive to build well. Using Wazuh lets the project focus on the interesting layers above collection.

### 5.2 Normalize everything

Each source has different event formats. The platform should convert them into a canonical schema before any correlation or detection.

### 5.3 Correlate, do not just alert

Single events are useful, but incidents are what analysts actually investigate. The system should group related signals into cases.

### 5.4 Treat detection as code

Rules should live in version control, be testable, and support CI validation.

### 5.5 Make the dashboard investigation-friendly

The UI should help answer:

- what happened,
- when it happened,
- which host was impacted,
- how confident the system is,
- what to do next.

---

## 6. System Components

## 6.1 Wazuh Layer

Wazuh provides:

- endpoint agents,
- log collection,
- FIM events,
- authentication events,
- policy and compliance visibility,
- built-in rule alerts.

### Role in this project

Wazuh becomes the endpoint telemetry backbone rather than the entire product.

### Ingestion strategy

Use one of the following:

- Wazuh alert JSON export,
- API polling,
- file-based log ingestion,
- webhook or message-based forwarding if available in your setup.

### Why this is useful

It gives the project immediate credibility and a large set of real telemetry types without building everything from scratch.

---

## 6.2 Suricata Layer

Suricata produces high-value network detections.

### Useful signals

- port scans,
- C2-like traffic,
- malicious IP hits,
- protocol anomalies,
- DNS tunneling patterns,
- suspicious HTTP requests.

### Why it matters

This adds the network side of XDR and makes the platform much more convincing than endpoint-only monitoring.

---

## 6.3 Zeek Layer

Zeek gives rich metadata rather than pure alerts.

### Useful logs

- `conn.log`
- `dns.log`
- `http.log`
- `ssl.log`
- `files.log`
- `notice.log`

### Why it matters

Zeek is excellent for correlation because it provides context around the session, host, domain, and protocol behavior.

---

## 6.4 Sigma Detection Layer

Sigma rules define the detection logic.

### Responsibilities

- load Sigma YAML rules,
- map normalized fields to rule fields,
- evaluate rules on incoming events,
- attach tactic and technique metadata,
- emit detection objects.

### Recommended rule organization

```text
rules/
├── brute_force/
├── persistence/
├── privilege_escalation/
├── lateral_movement/
├── exfiltration/
├── web_attack/
├── malware/
├── network_scan/
└── suspicious_activity/
```

### Rule metadata

Each rule should include:

- rule ID,
- title,
- description,
- MITRE tactic,
- MITRE technique,
- severity,
- confidence,
- false-positive notes,
- suppression hints,
- tags.

---

## 7. Normalized Event Model

All sources should map to a common schema.

### Example canonical event

```json
{
  "event_id": "uuid",
  "timestamp": "2026-05-29T12:00:00Z",
  "source": "wazuh",
  "host_id": "host-001",
  "host_name": "ubuntu-lab-01",
  "event_type": "authentication_failure",
  "user": "admin",
  "src_ip": "10.0.0.12",
  "dst_ip": null,
  "process_name": null,
  "process_id": null,
  "command_line": null,
  "file_path": null,
  "message": "Failed password for admin",
  "raw": {}
}
```

### Key fields

- `timestamp`
- `source`
- `host_id`
- `host_name`
- `event_type`
- `severity`
- `user`
- `src_ip`
- `dst_ip`
- `process_name`
- `command_line`
- `message`
- `raw`

This schema should be used for detection, storage, and correlation.

---

## 8. Correlation and Incident Engine

This is the main feature that makes the project unique.

## 8.1 Purpose

Instead of producing isolated alerts, the system should combine signals into meaningful incidents.

### Example pattern

- repeated failed logins,
- followed by a successful login,
- followed by sudo usage,
- followed by persistence creation,
- followed by suspicious outbound traffic.

This should become one incident, not five disconnected alerts.

---

## 8.2 Correlation rules

Correlation rules can be written in custom Python or in a rule DSL.

### Examples

- same host + same user + repeated auth failures within 10 minutes,
- same source IP hitting multiple services within a short time,
- same host generating endpoint and network alerts within a window,
- detection chain aligned to ATT&CK tactics.

---

## 8.3 Incident object

```json
{
  "incident_id": "uuid",
  "title": "Possible Linux Host Compromise",
  "severity": "critical",
  "confidence": 93,
  "status": "open",
  "host_id": "host-001",
  "first_seen": "2026-05-29T12:00:00Z",
  "last_seen": "2026-05-29T12:18:00Z",
  "related_alerts": ["alert-1", "alert-2", "alert-3"],
  "attack_story": [
    "Brute force authentication attempts",
    "Successful login from same source",
    "Privilege escalation detected",
    "Outbound connection to suspicious IP"
  ],
  "mitre_techniques": ["T1110", "T1068", "T1071"],
  "recommended_actions": [
    "Review authentication logs",
    "Confirm user activity",
    "Check for persistence",
    "Inspect outbound connections"
  ]
}
```

---

## 9. Threat Intelligence and Enrichment

## 9.1 External enrichment sources

- **AbuseIPDB** for reputation.
- **VirusTotal** for IPs, domains, and hashes.
- **MISP** for IOC feeds.
- Optional GeoIP/ASN lookup.

## 9.2 Enrichment workflow

1. Alert arrives.
2. Extract indicators such as IP, domain, hostname, or hash.
3. Query enrichment sources asynchronously.
4. Cache the result.
5. Attach metadata to the alert and incident.

### Example enriched alert fields

```json
{
  "abuse_score": 87,
  "country_code": "RU",
  "asn": "AS12345",
  "vt_malicious": 12,
  "vt_suspicious": 3
}
```

### Why this matters

It helps analysts decide whether the alert is likely benign, suspicious, or truly malicious.

---

## 10. Risk Scoring

Instead of showing a flat list of alerts, the system should compute risk.

### Inputs

- alert severity,
- alert confidence,
- ATT&CK stage,
- enrichment results,
- repeat frequency,
- host criticality,
- user sensitivity,
- correlation strength.

### Example score model

```text
Base severity:
Low = 10
Medium = 25
High = 50
Critical = 80

Modifiers:
- Known malicious IP: +15
- Multiple correlated alerts: +20
- Sensitive host: +10
- Suppressed / noisy rule: -10
```

### Output

- host risk score,
- incident risk score,
- user risk score,
- network segment risk score.

This creates a more enterprise-like experience.

---

## 11. Backend Architecture

## 11.1 FastAPI services

The backend should expose:

- ingestion endpoints,
- search and query endpoints,
- incident management endpoints,
- rule management endpoints,
- enrichment and health endpoints.

### Service modules

- `ingest.py`
- `normalize.py`
- `detect.py`
- `correlate.py`
- `enrich.py`
- `incident.py`
- `alerts.py`
- `rules.py`
- `health.py`

---

## 11.2 Background workers

Workers should handle:

- alert enrichment,
- Sigma evaluation,
- correlation windows,
- risk scoring,
- cache refresh,
- report generation.

### Queue options

- Redis Streams,
- Redis lists,
- asyncio queue for single-node labs.

Redis Streams is the better long-term choice.

---

## 11.3 Storage design

### PostgreSQL tables

- `hosts`
- `events`
- `alerts`
- `incidents`
- `incident_alerts`
- `rules`
- `suppression_windows`
- `enrichment_cache`
- `user_actions`
- `hunt_queries`

### Storage goals

- preserve raw events,
- query alerts efficiently,
- support filtering by host, severity, time, and technique,
- keep incident relationships explicit.

---

## 12. Example Database Schema

## 12.1 Hosts table

```sql
CREATE TABLE hosts (
    host_id UUID PRIMARY KEY,
    host_name TEXT NOT NULL,
    os_name TEXT,
    os_version TEXT,
    agent_type TEXT,
    first_seen TIMESTAMPTZ NOT NULL DEFAULT now(),
    last_seen TIMESTAMPTZ NOT NULL DEFAULT now(),
    tags JSONB DEFAULT '{}'::jsonb,
    criticality INT DEFAULT 1
);
```

## 12.2 Alerts table

```sql
CREATE TABLE alerts (
    alert_id UUID PRIMARY KEY,
    incident_id UUID NULL,
    host_id UUID REFERENCES hosts(host_id),
    rule_id TEXT NOT NULL,
    rule_name TEXT NOT NULL,
    severity TEXT NOT NULL,
    confidence TEXT NOT NULL,
    mitre_tactic TEXT,
    mitre_technique TEXT,
    source_ip INET,
    destination_ip INET,
    timestamp TIMESTAMPTZ NOT NULL,
    raw_event JSONB NOT NULL,
    enrichment JSONB DEFAULT '{}'::jsonb
);
```

## 12.3 Incidents table

```sql
CREATE TABLE incidents (
    incident_id UUID PRIMARY KEY,
    title TEXT NOT NULL,
    severity TEXT NOT NULL,
    confidence INT NOT NULL,
    status TEXT NOT NULL DEFAULT 'open',
    host_id UUID REFERENCES hosts(host_id),
    first_seen TIMESTAMPTZ NOT NULL,
    last_seen TIMESTAMPTZ NOT NULL,
    attack_story JSONB DEFAULT '[]'::jsonb,
    mitre_techniques JSONB DEFAULT '[]'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

## 12.4 Events table

Use partitioning if volume grows.

```sql
CREATE TABLE events (
    event_id UUID PRIMARY KEY,
    host_id UUID REFERENCES hosts(host_id),
    source TEXT NOT NULL,
    event_type TEXT NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL,
    normalized JSONB NOT NULL,
    raw JSONB NOT NULL
);
```

---

## 13. Frontend Specification

## 13.1 Main dashboard views

### Overview

- total alerts,
- active incidents,
- top risky hosts,
- current threat level,
- recent telemetry sources.

### Alerts view

- filter by severity,
- filter by host,
- filter by rule,
- filter by technique,
- filter by time range.

### Incident view

- attack timeline,
- linked alerts,
- enrichment results,
- analyst notes,
- response actions.

### Hunt view

- search over normalized data,
- saved queries,
- recent hunts,
- query templates.

### Rules view

- enabled rules,
- disabled rules,
- noisy rules,
- test rule against sample logs.

### Coverage view

- ATT&CK heatmap,
- detected techniques,
- missed techniques,
- source coverage by telemetry type.

---

## 14. Response and Playbooks

A strong project should not stop at detection.

## 14.1 Response actions

- isolate host,
- block IP,
- kill process,
- disable user,
- mark incident false positive,
- escalate incident,
- generate case notes.

## 14.2 Realistic lab-safe approach

In a lab, response actions can be simulated or executed through:

- SSH commands,
- host scripts,
- firewall rules,
- Wazuh active response,
- API-triggered local scripts.

## 14.3 Playbook examples

- brute force containment,
- suspicious outbound traffic review,
- privilege escalation response,
- ransomware containment,
- persistence investigation.

---

## 15. Detection Engineering Workflow

### Rule lifecycle

1. Write Sigma rule.
2. Validate syntax.
3. Map fields to normalized schema.
4. Test against sample events.
5. Measure false positives.
6. Add suppression if necessary.
7. Deploy rule.
8. Monitor accuracy.

### Rule quality metrics

- true positives,
- false positives,
- alert volume,
- suppression rate,
- incident conversion rate.

This makes the project look like a real detection engineering platform.

---

## 16. Threat Hunting Experience

The hunt layer should feel analyst-friendly.

### Features

- saved searches,
- query history,
- pivoting from alert to host to IP,
- timeline exploration,
- entity-based search,
- IOC lookups.

### Example hunt questions

- Which hosts contacted this IP?
- Which users failed authentication more than 10 times?
- Which hosts triggered both network and endpoint alerts?
- Which incidents started with brute force activity?

---

## 17. AI-Assisted Investigation Layer

This should assist analysts, not replace detections.

### Useful AI tasks

- summarize incidents,
- explain why a rule fired,
- generate next-step investigation suggestions,
- compare incidents,
- draft analyst notes.

### Example prompt input

```json
{
  "incident": {},
  "alerts": [],
  "enrichment": {},
  "recent_events": []
}
```

### Example output

- concise incident summary,
- likely attack chain,
- suspected technique,
- recommended analyst actions.

This makes the product feel modern without depending on AI for detection logic.

---

## 18. Docker and Lab Deployment

## 18.1 What should run in Docker

- PostgreSQL
- Redis
- optional admin tools like pgAdmin or Redis Insight

## 18.2 What should run outside Docker

- FastAPI backend
- worker processes
- Wazuh manager or existing security stack
- frontend dev server or static build

This keeps the lab flexible and easy to troubleshoot.

## 18.3 Docker Compose services

```yaml
services:
  postgres:
    image: postgres:16
    environment:
      POSTGRES_DB: openxdr
      POSTGRES_USER: openxdr
      POSTGRES_PASSWORD: change_me
    ports:
      - "5432:5432"

  redis:
    image: redis:7
    ports:
      - "6379:6379"
```

### Why this is enough

The platform needs durable storage and fast queueing, but the main app logic should remain visible and debuggable on the host.

---

## 19. Security Considerations

### Secrets handling

Store in `.env`:

- database credentials,
- API keys,
- threat intel keys,
- webhook URLs.

### Access control

- authenticated dashboard access,
- role-based permissions if possible,
- API key or token protection for ingestion,
- audit logging for analyst actions.

### Defensive safeguards

- rate limit ingestion,
- validate all incoming telemetry,
- sanitize raw event data,
- isolate lab response actions from production systems.

---

## 20. Logging and Audit Trail

The platform should log:

- ingestion success/failure,
- rule matches,
- suppression decisions,
- enrichment lookups,
- analyst actions,
- incident changes,
- response execution.

This makes debugging and evaluation much easier.

---

## 21. Testing Strategy

### Unit tests

- normalizer functions,
- Sigma rule parser,
- correlation logic,
- scoring logic,
- enrichment caching,
- API validation.

### Integration tests

- Wazuh event ingestion,
- Suricata event ingestion,
- Zeek event ingestion,
- alert generation,
- incident creation.

### Sample test datasets

- brute force SSH logs,
- malicious DNS traffic,
- suspicious HTTP requests,
- privilege escalation examples,
- synthetic IOC matches.

---

## 22. Suggested Repository Structure

```text
openxdr/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── api/
│   │   ├── core/
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── services/
│   │   └── workers/
│   ├── alembic/
│   └── tests/
├── frontend/
│   ├── src/
│   └── public/
├── rules/
│   ├── sigma/
│   └── correlation/
├── integrations/
│   ├── wazuh/
│   ├── suricata/
│   ├── zeek/
│   └── threat_intel/
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## 23. Roadmap

## Phase 1 — Foundation

- set up PostgreSQL and Redis,
- build FastAPI backend,
- define normalized schema,
- ingest Wazuh alerts,
- store raw and normalized events.

## Phase 2 — Detection

- add Sigma rule loading,
- create alert pipeline,
- build suppression logic,
- implement alert search endpoints.

## Phase 3 — Correlation

- create incident engine,
- group related alerts,
- build attack timelines,
- add risk scoring.

## Phase 4 — Multi-Source XDR

- ingest Suricata alerts,
- ingest Zeek logs,
- correlate network and endpoint events,
- enrich with threat intel.

## Phase 5 — Frontend and Response

- build dashboard,
- add hunt pages,
- add ATT&CK coverage views,
- add response playbooks.

## Phase 6 — Polish

- testing,
- documentation,
- sample datasets,
- demo videos,
- deployment guides.

---

## 24. Final Project Pitch

**OpenXDR** is an open-source security analytics and investigation platform that combines Wazuh, Suricata, Zeek, Sigma, and threat intelligence into a single correlation-driven interface. It focuses on incident reconstruction, risk scoring, and analyst workflows rather than merely displaying raw alerts.

### One-line summary

> An open-source mini XDR platform that transforms endpoint and network telemetry into correlated incidents, ATT&CK-mapped detections, and actionable investigations.

---

## 25. What Makes It Resume-Worthy

This project demonstrates:

- endpoint security knowledge,
- network security knowledge,
- detection engineering,
- alert correlation,
- threat intelligence enrichment,
- backend engineering,
- database design,
- security operations workflow understanding,
- analyst-focused product thinking.

That combination is stronger than a basic EDR clone because it shows you understand the whole security operations pipeline.
