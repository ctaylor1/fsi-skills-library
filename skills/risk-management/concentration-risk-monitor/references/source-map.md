# Source Map — concentration-risk-monitor

## Source hierarchy (highest first)

| Rank | Source (MCP integration) | Used for | Access |
| ---- | ------------------------ | -------- | ------ |
| 1 | **Risk-register / limit library** (versioned) | Single-name, sector, geography, product, absolute-cap, and diversification-floor limits and their bases | Read-only |
| 2 | **Exposure & finance data** (exposure book of record) | Per-book exposures, amounts, counterparty/sector/geography/product attribution, and the named bases (total exposure, eligible capital) | Read-only |
| 3 | **Pipeline / proposed-exposure feed** | Forward pre-onboarding checks (would a proposed exposure or migration newly breach a limit) | Read-only |
| 4 | **Third-party & operational-dependency inventory** | Cloud / AI / technology provider and operational-dependency scope and criticality | Read-only |
| 5 | **Reference data** | Counterparty-group hierarchy, sector/geography classification, provider normalization | Read-only |
| 6 | **Loss-event & scenario store** | Context that a concentration has previously materialized as loss or featured in a scenario | Read-only |
| 7 | **Prior open-alert store** | Deduplication of already-open exceptions across runs | Read-only |

The **limit library is the definition of record** for every threshold and basis. Never infer
a limit from exposures, a business line's assertion, or a prior run. If exposures and the
inventory disagree on scope (e.g., provider naming or counterparty-group rollup), cite both
and raise the ambiguity — do not resolve it silently.

## Citation format

`{system}:{ref}@{date}` — e.g.
`risk:book=BOOK-WHOLESALE;sector=Financials@2026-07-17` (a bucket),
`risk:book=BOOK-WHOLESALE;exposure=EXP-W1@2026-07-17` (a contributing exposure),
`pipeline:book=BOOK-WHOLESALE;proposed=PROP-1@2026-07-17` (a proposed exposure),
`risk:book=BOOK-STALE;exposures_as_of=2026-07-10@2026-07-17` (freshness), and each rule cites
`limits:rule_id=SECTOR-30@concentration-cfg-2026.07`. Every alert cites the measured bucket,
its top contributors, and the rule (with its config version).

## Freshness / effective dates

- Limits are a **versioned contract** (`config_version`); the pack records the version so a
  run is reproducible and an exception can be tied to the exact limit in force.
- Each book carries `exposures_as_of`. The monitor computes `staleness_days` against the run
  `as_of` and the `max_staleness_days` setting.
- **Stale data is flagged, never suppressed.** A stale book raises a freshness alert and every
  alert derived from it is marked `stale_input: true`; results are treated as low-confidence
  pending refreshed exposures, not silently dropped.

## Least-privilege operations (deployment)

- `limits.get(config_version)` → the versioned limit set (concentration, absolute-cap,
  diversification) with bases.
- `exposures.get(book_id, as_of)` → per-book exposures, amounts, dimension attribution, bases
  (paged).
- `pipeline.proposed(book_id)` → proposed / pending exposures for the forward check.
- `inventory.providers(as_of)` / `inventory.dependencies(as_of)` → third-party and
  operational-dependency scope.
- `refdata.resolve(counterparty|group|sector|geography|provider)` → normalized classifications.
- `alerts.open(scope)` → previously-open alert fingerprints for deduplication.

All read-only, deterministic, below the fixed timeout, with a durable `run_id`. Page large
exposure sets as resumable stages. The monitor writes **nothing** back to any system of
record — it only emits alerts and queue items for human review and adjudication.
