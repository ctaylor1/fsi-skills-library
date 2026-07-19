# Source Map — covenant-compliance-monitor

## Source hierarchy (highest first)

| Rank | Source (MCP integration) | Used for | Access |
| ---- | ------------------------ | -------- | ------ |
| 1 | **Executed credit agreement + amendments** (document intelligence) | The **definition of record** for every covenant: definition, calculation mechanics, thresholds, test dates, cure/grace terms, reporting requirements | Read-only |
| 2 | **Parsed covenant library** (versioned, `config_version`) | The machine-readable covenant definitions the monitor evaluates; human-verified extract of source 1 | Read-only |
| 3 | **Approved financial spreads** (bank-approved) | The numbers each financial and negative covenant is computed from (EBITDA, debt, fixed charges, TNW, baskets) | Read-only |
| 4 | **Borrower compliance certificate** | Borrower-reported covenant values and deliverable receipt, reconciled against the bank's independent calculation | Read-only |
| 5 | **Loan servicing / boarding system** | Facility master, obligor, test period, deliverable due dates and received dates | Read-only |
| 6 | **Prior open-alert store** | Deduplication of already-open exceptions across runs | Read-only |

The **credit agreement is the definition of record** for every covenant; the parsed covenant
library (`config_version`) is its versioned, human-verified machine form. Never infer a
threshold, calculation mechanic, or cure term from a spread, a borrower assertion, or a prior
run. The monitor **computes** covenant values only from **approved spreads** (source 3); it
never re-derives figures from raw financial statements or re-interprets ambiguous legal
covenant language on its own — an ambiguous or disputed definition is a human loan-documentation
and legal-counsel question (see [handoffs.md](handoffs.md)).

## Citation format

`{system}:{ref}@{date}` — e.g. `spread:facility=FAC-1001;period=2026-Q2@2026-07-17`,
`cert:facility=FAC-1001;period=2026-Q2@2026-07-17`, and each covenant cites
`covlib:covenant_id=LEV-MAX-400@covlib-2026.07`. Every alert cites the measured evidence
row(s) (the spread and/or certificate) **and** the covenant definition (with its
`config_version`). A reconciliation break additionally cites both the bank-computed value and
the borrower-reported value.

## Freshness / effective dates

- Covenant definitions are a **versioned contract** (`config_version`); the pack records the
  version so a run is reproducible and each exception ties to the exact covenant text in force
  at the test period.
- Each facility carries `spread_as_of` (the effective date of the approved spread the tests
  run on). The monitor computes `staleness_days` against the run `as_of` and the deployment's
  `max_staleness_days`.
- **Stale data is flagged, never suppressed.** A stale spread raises a freshness alert and
  every covenant result derived from it is marked `stale_input: true`; results are treated as
  low-confidence pending a refreshed, re-approved spread, not silently dropped.

## Least-privilege operations (deployment)

- `covlib.get(agreement_id, config_version)` → the versioned covenant set for a facility.
- `spreads.get(facility_id, test_period)` → the approved spread line items (paged).
- `certificate.get(facility_id, test_period)` → borrower-reported values + receipt dates.
- `servicing.facility(facility_id)` → facility master, obligor, deliverable schedule.
- `alerts.open(facility_id | portfolio)` → previously-open alert fingerprints for dedup.

All read-only, deterministic, below the fixed timeout, with a durable `run_id`. Page large
portfolios of facilities as resumable stages. The monitor writes **nothing** back to any
system of record — it only emits alerts and queue items for human credit review.
