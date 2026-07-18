# Source Map — best-execution-reviewer

## Source hierarchy (highest first)

| Rank | Source (MCP integration) | Used for | Access |
| ---- | ------------------------ | -------- | ------ |
| 1 | **OMS/EMS execution record** (position of record) | What was done: order, fills, venue, timestamps, commission, exception flag | Read-only |
| 2 | **Market & reference data** | Benchmark price (arrival mid / NBBO/EBBO / interval VWAP), venue/MIC taxonomy, tick/lot conventions | Read-only |
| 3 | **Best-execution policy config** (versioned) | Price tolerance & material bps, latency ceiling, minimum fill rate, cost cap, effective approved-venue list, per-client-class weights | Read-only |
| 4 | **Communications archive** | Documented exception rationale, client instructions, manual-route notes | Read-only |
| 5 | **Post-trade / clearing** | Settlement confirmation for likelihood-of-settlement context | Read-only |

Never substitute a trader assertion or the OMS comment for the execution record. If the
execution record and market data conflict (e.g. a benchmark that predates the order), cite
both and flag it as `not_evaluable` or a data-quality note — do not silently pick one.

## Citation format

`{system}:{ref}@{timestamp}` — e.g. `oms:oms=US-Equities;exec=X-003@2026-07-14T10:10:03`.
Every fired finding cites the specific execution rows and the benchmark/threshold it failed.

## Freshness / effective dates

- Policy config (thresholds, approved-venue list, client-class weights) is a **versioned
  contract**; the output records the `policy_version` used so a review is reproducible.
- The **benchmark must be the one effective at the order's decision time** (arrival), not a
  later or session-close price; benchmark_type is recorded per execution.
- The **approved-venue list effective on the trade date** governs the venue check — a venue
  added or removed after the trade must not change the finding.

## Least-privilege operations (deployment)

- `oms.executions(scope, from, to)` → bounded, paged execution rows with source_ref.
- `marketdata.benchmark(symbol, ts, type)` → benchmark price at/near the arrival timestamp.
- `refdata.venue(mic)` → normalized venue/MIC and status.
- `policy.get('bestex', version)` → thresholds + approved-venue list + weights.
- `comms.rationale(order_id)` → documented exception rationale reference (no free-text
  content beyond what evidences the finding).

All read-only, deterministic, durable `review_id`, below the fixed timeout; page long
execution populations as resumable stages.
