# Source Map — pricing-hedging-scenario-calculator

## Source hierarchy (highest first)
| Rank | Source (MCP integration) | Used for | Access |
| ---- | ------------------------ | -------- | ------ |
| 1 | Risk system / position record | Position DV01, direction | Read-only |
| 2 | Hedge-instrument reference | Hedge DV01 per unit | Read-only |
| 3 | Reference data | Scenario/curve normalization | Read-only |

Risk parameters come from the risk system; the worksheet records the parameters used and never
prices firmly or executes.

## Citation format
`{system}:{ref}@{as_of}` — e.g. `risk:trade=TRD-9;dv01@2026-07-18`. The worksheet records the
trade id and the parameters used.

## Freshness / effective dates
- DV01/parameters are used **as of** the supplied as_of; the estimate is linear and first-order.

## Least-privilege operations (deployment)
- `risk.read_position(trade_id)` → DV01 + direction — read-only, bounded.
- `ref.read_hedge(hedge_instrument)` → hedge DV01 — read-only.
Durable `scenario_id`; deterministic; below the fixed timeout; no mutation; no pricing/execution.
