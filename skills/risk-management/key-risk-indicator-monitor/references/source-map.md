# Source Map — key-risk-indicator-monitor

## Source hierarchy (highest first)

| Rank | Source (MCP integration) | Used for | Access |
| ---- | ------------------------ | -------- | ------ |
| 1 | **KRI / risk-register threshold library** (versioned) | Amber/red bands, direction, seasonal baselines, ownership, criticality | Read-only |
| 2 | **Metric / observation feed** (KRI data marts, finance & operational data) | Latest KRI values and history per period | Read-only |
| 3 | **Loss-event / incident store** | Linkage of a KRI breach to open incidents or loss events | Read-only |
| 4 | **Scenario / stress library** | Context for whether a trend maps to a modeled scenario | Read-only |
| 5 | **Third-party inventory** | Resolving vendor/service KRIs to the underlying third party | Read-only |
| 6 | **Prior open-alert store** | Deduplication of already-open exceptions across runs | Read-only |

The **threshold library is the definition of record** for every band, direction, and seasonal
baseline. Never infer a threshold from an observation, a risk owner's assertion, or a prior
run. If the observation feed and the library disagree on scope (e.g., a KRI's unit or
direction), cite both and raise the ambiguity — do not resolve it silently.

## Citation format

`{system}:{ref}@{date}` — e.g. `kri:kri_id=KRI-OPS-FAILPAY;period=2026-07@2026-07-17`
(observation), `register:kri_id=KRI-OPS-FAILPAY@kri-cfg-2026.07` (the versioned threshold),
`kri:kri_id=KRI-MR-VAR;observation_as_of=2026-07-05@2026-07-17` (freshness), and an incident
reference `incidents:kri_id=KRI-OPS-FAILPAY;incident=INC-2026-0142@2026-07-17`. Every alert
cites the measured observation row(s) and the threshold (with its config version).

## Freshness / effective dates

- Thresholds are a **versioned contract** (`config_version`); the pack records the version so a
  run is reproducible and an exception can be tied to the exact appetite text in force.
- Each KRI carries `observation_as_of`. The monitor computes `staleness_days` against the run
  `as_of` and the run's `max_staleness_days`.
- **Stale data is flagged, never suppressed.** A stale KRI raises a freshness alert and every
  alert derived from it is marked `stale_input: true`; results are treated as low-confidence
  pending refreshed observations, not silently dropped.
- **Missing data is surfaced, not assumed clean.** A null or absent latest observation raises a
  data-quality alert rather than a PASS.

## Least-privilege operations (deployment)

- `register.get(kri_library, config_version)` → the versioned KRI thresholds, directions, and
  seasonal baselines.
- `metrics.observations(kri_id, from, to)` → the observation history (paged).
- `incidents.linked(kri_id)` → open incidents / loss events tied to the KRI.
- `thirdparty.resolve(kri_id)` → the underlying vendor/service for a third-party KRI.
- `alerts.open(scope)` → previously-open alert fingerprints for deduplication.

All read-only, deterministic, below the fixed timeout, with a durable `run_id`. Page large
observation histories as resumable stages. The monitor writes **nothing** back to any system of
record — it only emits alerts and queue items for human review.
