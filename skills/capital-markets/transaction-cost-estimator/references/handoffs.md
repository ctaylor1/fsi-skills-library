# Adjacent-Skill Handoffs — transaction-cost-estimator

Produces a TCA workbook (`tca_id`) and stops. It does not route/execute/amend orders or judge
execution quality.

## Downstream / lateral (route to)
| Skill | When |
| ----- | ---- |
| `best-execution-reviewer` | Whether execution met the best-execution obligation (venue/routing/price quality) |
| `order-allocation-validator` | Validating how an executed order was allocated across accounts |

## Upstream (may call this skill)
Execution-quality and trading-analytics workflows request a TCA estimate. Interactive
(`aws-fsi-scheduled-agent: no`).

## Duplicate-execution prevention
- This skill **estimates cost only**; it never routes/executes/amends or asserts best
  execution — those belong to the trader/OMS and `best-execution-reviewer`.
- Downstream reuses the `tca_id` components rather than recomputing.
