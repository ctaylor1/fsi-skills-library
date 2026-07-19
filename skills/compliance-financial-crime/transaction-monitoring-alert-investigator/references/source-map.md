# Source Map — transaction-monitoring-alert-investigator

## Source hierarchy (highest first)

| Rank | Source (MCP integration) | Used for | Access |
| ---- | ------------------------ | -------- | ------ |
| 1 | **Escalated alert + triage evidence** (transaction-monitoring / case system) | The alert under investigation, its scenario, and first-line triage rationale | Read-only |
| 2 | **Typology scenario library** (versioned) | Structuring, pass-through, geography, velocity, cash-intensity thresholds | Read-only |
| 3 | **KYC / CDD / risk-rating store** | Customer & beneficial-owner profile, expected activity, risk rating | Read-only |
| 4 | **Core banking / transactions & accounts** | Transaction ledger, accounts, instruments, channels (the evidence) | Read-only |
| 5 | **Counterparty / network graph + reference data** | Counterparty resolution, geography, relationship network | Read-only |
| 6 | **Sanctions / adverse-media screening results** | Screening context for parties and counterparties | Read-only |
| 7 | **Prior-case / SAR index** | Deduplication against previously-open cases; prior dispositions | Read-only |

The **escalated alert and the versioned scenario library are the definition of record** for what
is being investigated and against which thresholds. Never infer a threshold from the transaction
data, an analyst's assertion, or a prior run. If the KYC store and the transactions disagree
(e.g., expected vs observed activity), cite both and raise the ambiguity — do not resolve it
silently.

## Citation format

`{system}:{ref}@{date}` — e.g. `txn:subject=CUST-1001;txn_id=T-1001-06@2026-07-17`,
`subject:subject=CUST-1001;geo_exposure=high_risk@2026-07-17`, and each rule cites
`rules:rule_id=STRUCT-CTR-10K@aml-typology-cfg-2026.07`. Every indicator cites the measured
evidence row(s) and the rule (with its config version); every chronology row cites its
transaction.

## Freshness / effective dates

- Thresholds are a **versioned contract** (`config_version`); the pack records the version so a
  run is reproducible and an indicator ties to the exact scenario logic in force.
- Each subject carries `data_as_of`. The monitor computes `staleness_days` against the run
  `as_of` and the configured `max_staleness_days`.
- **Stale data is flagged, never suppressed.** A stale subject raises a freshness indicator and
  every indicator derived from it is marked `stale_input: true`; results are treated as
  low-confidence pending refreshed data, not silently dropped.

## Least-privilege operations (deployment)

- `alerts.get(alert_id)` → the escalated alert, its scenario, and triage evidence.
- `scenarios.get(config_version)` → the versioned typology threshold set.
- `kyc.profile(subject_id)` → risk rating, expected activity, CDD data.
- `txns.list(subject_id, window)` → transactions, accounts, instruments (paged).
- `entities.resolve(counterparty|account|customer)` → normalized identities + geography.
- `screening.results(subject_id)` → sanctions / adverse-media context (read-only).
- `cases.open(subject_id)` → previously-open case fingerprints for deduplication.

All read-only, deterministic, below the fixed timeout, with a durable `run_id`. Page large
transaction histories as resumable stages. The monitor writes **nothing** back to any case system
or system of record — it only emits indicators, an evidence bundle, and queue items for human
review.
