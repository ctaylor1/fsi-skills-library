# Adjacent-Skill Handoffs — desk-pnl-risk-attribution-pack

Produces a cited P&L-attribution packet (`attribution_id`) and stops. It does not adjust,
restate, book, or sign off P&L.

## Downstream (route the human/reviewer to)
| Downstream skill | When | Handoff artifact |
| ---------------- | ---- | ---------------- |
| `trade-break-resolver` | A trade/position break underlies the residual (fills/positions don't reconcile) | desk id + break evidence |
| `best-execution-reviewer` | Execution-quality review (not attribution) | desk id + order refs |

## Upstream (may call this skill)
Product-control and desk-supervision workflows may request a P&L-attribution packet. This skill is
interactive (`aws-fsi-scheduled-agent: no`).

## Duplicate-execution prevention
- This skill only **reconciles and evidences** the attribution; it never adjusts or signs off
  P&L — those belong to product control.
- Downstream reuses the `attribution_id` evidence rather than recomputing.
