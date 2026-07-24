# Adjacent-Skill Handoffs — pricing-hedging-scenario-calculator

Produces an illustrative linear scenario/hedge worksheet (`scenario_id`) and stops. It does not
price firmly, quote, or execute.

## Downstream (route the human/analyst to)
| Downstream skill | When | Handoff artifact |
| ---------------- | ---- | ---------------- |
| `transaction-cost-estimator` | Expected transaction cost for filling the hedge/position size | instrument + size |
| `client-rfq-preparation-brief` | Client-facing RFQ context is assembled | trade id + client |
| `trade-break-resolver` | Position/risk figures don't reconcile | trade id + break |

## Upstream (may call this skill)
Structuring and sales-trading workflows may request scenario/hedge sizing. This skill is
interactive (`aws-fsi-scheduled-agent: no`).

## Duplicate-execution prevention
- This skill only **estimates scenarios and hedge sizing**; it never prices firmly or executes —
  those belong to the desk.
- Downstream reuses the `scenario_id` worksheet rather than recomputing.
