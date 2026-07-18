# Source Map — performance-attribution-builder

## Source hierarchy (highest first)

| Rank | Source (MCP integration) | Used for | Access |
| ---- | ------------------------ | -------- | ------ |
| 1 | **Performance / risk system** (book of record) | Official portfolio and benchmark returns, segment returns, GIPS composite membership | Read-only |
| 2 | **PMS / OMS / accounting** | Position weights, segment/classification map, currency of each holding, cash | Read-only |
| 3 | **Market / index data** | Benchmark constituents and segment benchmark returns, FX rates / currency returns | Read-only |
| 4 | **Research / classification** | Sector/factor/instrument taxonomy used for the segmentation | Read-only |
| 5 | **Compliance rules / mandate** | Marketing-review requirements, benchmark policy, disclosure rules | Read-only |
| 6 | Approved **attribution config** (model, tolerances, template) — versioned | Method, reconciliation/weight tolerances, template | Read-only |

The **performance/risk system is the system of record** for realized returns; the attribution is
reconciled bottom-up to its official portfolio and benchmark returns. PMS/accounting is the
authority on weights and classification; market/index data on benchmark segment returns and FX.
This skill reads only — it never writes back a return, a decision, or a delivery.

## Citation format

`{system}:{ref}@{date/version}` — e.g. `perfsys:seg=EQ-US@2026-06-30`,
`perfsys:signoff=PM-4471@2026-07-16`, `pms:port=FUND-GLBL-EQ@2026-06-30`,
`marketdata:fx=EURUSD@2026-06-30`, `config:attribution@2026.07`. Every segment row carries a
citation; the portfolio/benchmark returns and every recorded approval carry citations. A figure
with no citable source is a `needs-data` open item, never an assumed value.

## Freshness / effective dates

- The attribution is for a **single, closed period** (`period.from`..`period.to`); returns must be
  final/official for that period, not intraperiod estimates.
- Segment returns and weights must be on a **consistent classification and period basis** across
  the portfolio and the benchmark.
- The bottom-up portfolio and benchmark returns are **reconciled to the official book-of-record
  returns** within `official_tolerance`; a break is raised as an open item, not silently accepted.
- `model`, tolerances, and the template are **versioned contracts**; the versions are recorded on
  the manifest (`config_version`, `template_version`) for reproducibility and review.

## Least-privilege operations (deployment)

- `perfsys.returns(portfolio_id, benchmark_id, period)` → official + segment returns — read-only.
- `pms.weights(portfolio_id, period, classification)` → segment weights + currency — read-only, bounded.
- `marketdata.segment_returns(benchmark_id, period)` / `marketdata.fx(period)` → benchmark and
  currency returns — read-only.
- `config.get('attribution', version)` — read-only.
No mutation from this skill. The assembled attribution is a **draft**; any external/marketing use
or system-of-record change is a separate, human-approved step via the approval broker. Client- or
composite-confidential figures stay within the deployment's residency boundary.
