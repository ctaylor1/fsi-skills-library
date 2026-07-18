# Source Map — mandate-compliance-monitor

## Source hierarchy (highest first)

| Rank | Source (MCP integration) | Used for | Access |
| ---- | ------------------------ | -------- | ------ |
| 1 | **Mandate / IPS rule library** (versioned) | Mandate, guideline, regulatory, concentration, ESG, and restriction limits | Read-only |
| 2 | **PMS / OMS positions** (holdings book of record) | Portfolio holdings, NAV, asset class, ratings, look-through | Read-only |
| 3 | **OMS proposed / pending trades** | Pre-trade compliance checks (would a proposed order breach a limit) | Read-only |
| 4 | **Market & reference data** | Prices, issuer/sector classification, ratings, ESG scores | Read-only |
| 5 | **Restricted / prohibited lists** (sanctions, firm-restricted, watch) | Restriction-rule membership | Read-only |
| 6 | **Prior open-alert store** | Deduplication of already-open exceptions across runs | Read-only |

The **rule library is the definition of record** for every limit. Never infer a limit from
holdings, a portfolio manager's assertion, or a prior run. If positions and the rule library
disagree on scope (e.g., asset-class tagging), cite both and raise the ambiguity — do not
resolve it silently.

## Citation format

`{system}:{ref}@{date}` — e.g. `pms:portfolio=FUND-A;sector=Technology@2026-07-16`,
`pms:portfolio=FUND-A;security=US_SANCTION_1@2026-07-16`,
`oms:portfolio=FUND-A;trade=PT-1@2026-07-17`, and each rule cites
`rules:rule_id=CONC-ISSUER-5@mandate-cfg-2026.07`. Every alert cites the measured evidence
row(s) and the rule (with its config version).

## Freshness / effective dates

- Limits are a **versioned contract** (`config_version`); the pack records the version so a
  run is reproducible and an exception can be tied to the exact rule text in force.
- Each portfolio carries `holdings_as_of` (and `prices_as_of`). The monitor computes
  `staleness_days` against the run `as_of` and the mandate's `max_staleness_days`.
- **Stale data is flagged, never suppressed.** A stale portfolio raises a freshness alert
  and every alert derived from it is marked `stale_input: true`; results are treated as
  low-confidence pending refreshed positions, not silently dropped.

## Least-privilege operations (deployment)

- `rules.get(mandate_id, config_version)` → the versioned limit set for a mandate.
- `pms.holdings(portfolio_id, as_of)` → positions, NAV, classifications (paged).
- `oms.proposed_trades(portfolio_id)` → pending orders for pre-trade checks.
- `refdata.resolve(security|issuer|sector|rating|esg)` → normalized classifications.
- `restrictions.list(as_of)` → restricted/prohibited securities.
- `alerts.open(mandate_id)` → previously-open alert fingerprints for deduplication.

All read-only, deterministic, below the fixed timeout, with a durable `run_id`. Page large
books of record as resumable stages. The monitor writes **nothing** back to any system of
record — it only emits alerts and queue items for human review.
