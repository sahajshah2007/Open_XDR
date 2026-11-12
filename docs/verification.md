# TwinTrace Lab v0.4 verification

Verified locally on 5 November 2026. Existing features were checked before cleanup,
checked after cleanup, and checked again after implementing comparison/configuration
features. [Cleanup details](cleanup.md) record the roughly 47 MB removed.

## Current checks

- Backend: 77 tests passed. The changed failed-run case was also checked separately.
- Frontend: ESLint, TypeScript and Vite production build passed.
- Live migration: `0003_detection_profiles`. Every pre-upgrade record ID was retained:
  14 hosts, 142 events, 273 alerts, 16 incidents, 14 experiment runs and one user.
- Live PostgreSQL/Redis/Celery: three paired experiments, saved configuration creation,
  use in a new run, and exact fingerprint preservation during replay all passed.
- Chrome at 1440 × 1080 and 390 × 844: five comparison tabs, A/B creation, configuration
  creation and persistence, single-run configuration selection, pinned replay,
  mismatched-fixture suppression, legacy unknown-setting labels, two comparison
  exports, responsive forms and navigation. No JavaScript errors or document overflow.
- Original desktop/mobile workflows still passed: overview, investigations, assets,
  original evidence, defense, notebook and settings, plus seeded replay, six experiment
  views, report downloads, flow controls, six interview chapters and presentation mode.
- The standalone comparison HTML opened successfully and printed to PDF.

## Observed paired results

Default local rules, fixture version 1, seed 42. A is Baseline in each case.

| Scenario | B configuration | Observed change |
| --- | --- | --- |
| DNS detection gap | DNS fixture coverage | TP +1, FN −1; DNS technique missed → detected |
| Noisy sensor | Higher Wazuh threshold | FP −1, TN +1 |
| SSH brute force | Higher Wazuh threshold | TP −3, FN +3; simulated port blocking no longer proposed |

All results came from actual event-linked alerts, independent fixture labels,
and saved per-run detector inputs. These tiny synthetic fixtures are educational
examples, not operational accuracy estimates. Queue load affects latency;
application code and response-policy versions are not pinned by configuration
snapshots. Real containment remained false. Optional live Neo4j was not exercised.

Saved records from both API and browser validation remain available for demos.
Comparison HTML and JSON downloads include the detector snapshots and methodology.

- [Comparison screenshot](screenshots/experiment-comparison.png)
- [Mobile comparison screenshot](screenshots/comparison-mobile.png)

---

# TwinTrace Lab v0.3 verification

Verified locally on 5 November 2026. All response effects are simulated.

## Automated and browser checks

- Backend: 65 tests passed; two dependency deprecation warnings.
- Frontend: ESLint, TypeScript and Vite production build passed.
- Docker: PostgreSQL and Redis healthy; API migration reached `0002_experiments`;
  backend, worker, scheduler and static frontend started successfully.
- Chrome: new experiment creation and same-seed replay, all six experiment views,
  stepping/scrubbing/speed controls, HTML/JSON/CSV downloads, standalone report opening and PDF printing, six guide chapters,
  image loading, presentation mode, keyboard navigation, and mobile navigation.
- Checked desktop 1440 × 1080 and mobile 390 × 844 with no document overflow and
  no browser JavaScript errors. Existing overview, investigations, assets, evidence,
  defense, notebook and settings views also passed; brief download and copy worked.
- The default recorded connectivity model keeps reused synthetic IP addresses
  separated between runs. Tests cover reachability to the appropriate critical
  asset without inventing endpoint identities from address-only telemetry.

## Live PostgreSQL / Redis / Celery scenarios

These runs used the real broker and worker, not the direct task calls in isolated
unit tests. Seed 42, fixture version 1, default enabled local rules.

| Scenario | Events | TP | FP | FN | TN | Model assertions passed |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| SSH brute force | 4 | 3 | 0 | 0 | 1 | 1 |
| Web shell | 3 | 3 | 0 | 0 | 0 | 1 |
| Lateral movement | 3 | 2 | 0 | 0 | 1 | 1 |
| Credential reuse | 2 | 2 | 0 | 0 | 0 | 2 |
| Benign maintenance | 3 | 0 | 0 | 0 | 3 | 0 |
| DNS detection gap | 2 | 0 | 0 | 1 | 1 | 0 |
| Noisy sensor | 2 | 0 | 1 | 0 | 1 | 0 |

All seven completed, all 21 export requests succeeded, and all recorded real
containment as false. The intentional miss and false positive were retained.
Browser checks additionally created clearly named validation runs and replays.
Demo runs remain in experiment history for presentations. Original imported
records (95 events, 241 alerts, four incidents and one host before replay) were
preserved during migration; new experiments add their own evidence.

These tiny, labeled synthetic fixtures are not a benchmark of operational threat
detection. Optional live Neo4j execution was not exercised in this verification.

## Visuals

- [Interview guide screenshot](screenshots/interview-guide.png)
- [Recorded flow screenshot](screenshots/recorded-flow.png)
- [Generated illustration prompt and provenance](visual-assets.md)
