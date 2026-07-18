# Source Map — investment-thesis-monitor

## Source hierarchy (highest first)

| Rank | Source (MCP integration) | Used for | Access |
| ---- | ------------------------ | -------- | ------ |
| 1 | **Thesis register** (controlled content library) | The active thesis: direction, owner, documented KPIs, catalysts, price target / stop, monitored risks, `thesis_asof` | Read-only |
| 2 | **PMS/OMS** | Holdings/position linkage (which theses map to live positions) | Read-only |
| 3 | **Market data** | Price and price date for target/stop breach | Read-only |
| 4 | **Research / estimates** | KPI prints, catalyst status, consensus-estimate revisions, filings/news flags | Read-only |
| 5 | **Risk / performance systems** | Context for escalation (not a decision input) | Read-only |
| 6 | **Monitor config** (versioned) | Tolerances, revision %, staleness window, lookback, escalation mapping | Read-only |

The **thesis register is the position of record for what the thesis claims**. Never
substitute a headline or a price move for the register's documented expectation. If a data
source conflicts with the register (e.g., a KPI defined differently), cite both and flag for
the analyst rather than resolving silently.

## Citation format

`{system}:{ref}@{observed_at}` — e.g. `research:th=TH-ACME;kpi=subscriber_growth;q=Q2@2026-07-15`,
`marketdata:th=TH-ACME;px=close@2026-07-16`. Every fired signal cites the specific evidence
rows and the observation date used, so an analyst can trace each alert to its source.

## Freshness / effective dates (critical for a scheduled monitor)

- Every evidence row carries an `observed_at` (or `price_asof`). The monitor computes its age
  against the scheduled-run `as_of` and **will not fire a signal on evidence older than
  `max_staleness_days`** (default 21) — stale evidence is `not_evaluable`.
- A thesis with **no fresh evidence at all** is surfaced as a `freshness_gaps` item (a data /
  feed problem for the analyst to refresh), never as a thesis breach.
- Config (tolerances, escalation mapping) is a **versioned contract**; the run records
  `config_version` so an alert is reproducible.
- `lookback_days` (default 90) bounds the news/observation window; state it in the output.

## Least-privilege operations (deployment)

- `thesis.register(book_id, as_of)` → active theses with documented expectations + owners.
- `positions.read(book_id)` → position linkage (read-only).
- `marketdata.quote(security, as_of)` → price + price date.
- `research.observations(security, from, to)` → KPI prints, catalyst status, estimate
  revisions, filing/news flags (each with an observation date + source ref).
- `config.get('thesis-monitor', version)` → tolerances + escalation mapping.

All read-only, deterministic, durable `monitor_run_id`, below the fixed timeout; page long
books as resumable stages. The monitor stages a queue only — it never writes to the register,
PMS/OMS, or research system of record.
