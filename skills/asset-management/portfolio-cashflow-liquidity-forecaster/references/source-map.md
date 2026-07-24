# Source Map — portfolio-cashflow-liquidity-forecaster

## Source hierarchy (highest first)

| Rank | Source (MCP integration) | Used for | Access |
| ---- | ------------------------ | -------- | ------ |
| 1 | **Transfer agent / investor register** | Subscriptions and redemptions (pending, noticed, settled), notice periods | Read-only |
| 2 | **Custodian / PMS holdings & cash** | Opening cash, coupons, dividends, maturities, the cash-of-record balance | Read-only |
| 3 | **Collateral-management system** | Projected margin calls (post = outflow) and collateral returns (inflow) | Read-only |
| 4 | **Operations / treasury calendar** | Known funding needs (settlements, capital calls, fees, expenses) | Read-only |
| 5 | **Market/financial data** | Coupon/maturity schedules, FX for multi-currency normalization | Read-only |
| 6 | **Analyst-supplied scenarios** | Category multipliers, date shifts, and the scenario set (the analyst owns these) | Analyst input |
| 7 | **Liquidity config** (versioned) | Category set, bucket conventions, tie-out tolerance, reconciliation targets | Read-only |

A **cash flow is only as good as its source.** Every cash flow, the opening cash, and every
scenario must resolve to one of the above with a dated citation. A confirmed/settled figure
outranks an estimate; when they conflict, keep the confirmed figure as the anchor and record the
estimate as an explicit, sourced override. **The skill never invents a cash flow or a scenario**
— scenarios are analyst-supplied and logged as such.

## Citation format

`{source}:{ref}@{date}` — e.g. `ta:redemption notices@2026-07-20`,
`custody:maturity ladder@2026-07`, `cm:projected margin call@2026-08`,
`risk-committee:stress menu S2@2026-07`. Each `assumptions_log` entry carries `provenance` (the
source class) and `citation` (the specific ref+date). `scripts/validate_output.py` rejects any
assumptions-log entry missing either.

## Freshness / effective dates

- **`as_of`** stamps when the cash flows and balances were read; **`forecast_start`** anchors the
  opening cash and the first bucket. State both in the output.
- **Cash flows are point-in-time** as of `as_of`; do not mix flows read on different dates within
  one forecast without noting it.
- **`config_version`** (category set, bucket conventions, tolerance, reconciliation targets) is a
  **versioned contract**; the output records it so a forecast is reproducible.
- The **`inputs_hash`** binds the forecast to the exact numeric inputs used; re-running the same
  inputs reproduces the same `forecast_id` and the same ladder.

## Durable case / job IDs

`forecast_id = pclf-{portfolio_id}-{as_of}-{inputs_hash}`, where `inputs_hash` is a SHA-256 over
the normalized numeric inputs (opening cash, bucket dates, cash flows, scenario parameters,
reconciliation targets). Identical inputs reproduce the identical `forecast_id`; changing any
input changes the hash, so the audit trail shows what moved. Downstream skills reference the
forecast by `forecast_id` rather than rebuilding it.

## Least-privilege operations (deployment)

- `transferagent.read(fund_id, as_of)` → pending/noticed subscriptions and redemptions with refs.
- `custody.read(portfolio_id, as_of)` → cash balance, coupon/dividend/maturity schedule.
- `collateral.read(portfolio_id, as_of)` → projected margin calls and collateral returns.
- `opscalendar.read(fund_id, window)` → known funding obligations.
- `config.get('pclf', version)` → category set, bucket conventions, tolerance, reconciliation targets.
All read-only, deterministic, durable `forecast_id`, below the fixed timeout. This skill makes
**no writes**; delivery to a committee, board, client, or system of record is a separate,
human-approved step.
