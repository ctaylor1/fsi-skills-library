# Adjacent-Skill Handoffs — trade-break-resolver

This skill owns the **plan → approve → execute → verify → audit** lifecycle for a confirmed
trade break. It does not diagnose-only, monitor settlement, or do regulatory reporting.

## Upstream (hands a confirmed break here)

| Upstream source | Handoff artifact |
| --------------- | ---------------- |
| `post-trade-settlement-monitor` surfaces a settlement fail/aging item that resolves to a correctable booking break | `break_id`, `trade_id`, type, evidence |
| `trade-confirmation-explainer` review that identifies a booking-vs-confirmation discrepancy | `break_id` + evidence + proposed repair |

## Downstream / lateral (route instead of acting)

| Skill | When |
| ----- | ---- |
| `transaction-reporting-quality-checker` | The break is (or the repair triggers) a regulatory transaction-reporting issue; the corrected trade needs re-reporting |
| `best-execution-reviewer` | The matter is execution-quality / venue / routing, not a booking break |
| `market-surveillance-alert-investigator` | The discrepancy signals potential misconduct, not an operational break |
| `corporate-action-interpreter` | The "break" is an unprocessed corporate action, not a booking error |
| `margin-collateral-optimizer` | The matter is a margin/collateral call, not a trade break |
| Human authority / desk supervisor / trade control | Repair is out-of-catalog, over-limit, or irreversible |

## Duplicate-execution prevention

- Only this skill executes the repair via the firm OMS/EMS; upstream monitoring/diagnosis
  skills must not also amend or rebook.
- Execution is keyed by `plan_id` + step idempotency keys — re-invocation never double-applies.
- If another workflow (or the counterparty/clearing side) already corrected the trade, the
  precondition check fails and this skill halts rather than re-applying.
