# Source Map — investment-data-quality-exception-detector

## Source hierarchy (highest first)

| Rank | Source (MCP integration) | Used for | Access |
| ---- | ------------------------ | -------- | ------ |
| 1 | **Security master / reference data** (position of record for identity) | Instrument keys, identifiers (ISIN/CUSIP/SEDOL/ticker), asset class, mappings | Read-only |
| 2 | **Market-data / pricing feed** (position of record for prices) | Current + prior price, price as-of, currency | Read-only |
| 3 | **Classification / analytics feeds** (per vendor) | Sector/rating/index classifications, risk & analytic factors | Read-only |
| 4 | **DQ config** (versioned) | Staleness/move thresholds, required-factor sets, per-type severities, priority mapping | Read-only |

Every check works over an **approved feed** only. Never substitute an assertion or a
computed guess for a feed value. When two approved sources disagree, cite both, raise an
exception, and route it — do not resolve it here.

## Citation format

`{system}:{ref}@{as_of}` — e.g. `px:inst=INS-1003;src=vendorA@2026-07-07` or
`sec-master:inst=INS-1005;isin=US5949181045@2026-07-17`. Every exception cites the specific
row(s) behind it and the as-of time used to judge staleness/moves.

## Freshness / effective dates

- **Snapshot `as_of`** anchors every staleness and day-over-day comparison; it is recorded in
  the queue and in each `exception_queue_id`.
- **Price as-of** per row drives `stale_price`; a missing as-of makes staleness
  not-evaluable (never assumed fresh).
- **DQ config** (thresholds, required-factor sets, severities, priority map) is a **versioned
  contract**; the queue records `config_version` so a sweep is reproducible.

## Durable identifiers

- `exception_queue_id` = `idqed-{portfolio}-{as_of}-{config_version}-{NNNN}` binds the queue
  to the exact snapshot, config, and run so downstream skills reference stable items.
- `exception_id` = `{exception_queue_id}::{type}::{NN}` is stable for a given snapshot+config,
  letting the reconciler or steward pick up a specific item without re-detecting.

## Least-privilege operations (deployment)

- `secmaster.read(universe, as_of)` → instruments + identifiers + mappings.
- `pricing.read(instrument_keys, as_of, with_prior=true)` → current + prior price + as-of.
- `refdata.read(instrument_keys, schemes, feeds)` → classifications + factors per feed.
- `config.get('dq', version)` → thresholds, required-factor sets, severities, priority map.

All read-only, deterministic, durable `exception_queue_id`, below the fixed timeout; page
long universes as resumable stages. No write, correct, suppress, or close operation exists in
this skill.
