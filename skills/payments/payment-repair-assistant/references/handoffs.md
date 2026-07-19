# Adjacent-Skill Handoffs — payment-repair-assistant

This skill owns the **plan → approve → execute → verify → audit** lifecycle for an approved
payment-exception case. It does not diagnose, investigate, adjudicate fraud or screening,
reconcile settlement, or handle disputes.

## Upstream (hands an approved case here)

| Upstream source | Handoff artifact |
| --------------- | ---------------- |
| `payment-exception-investigator` | `case_id`, `payment_id`, `end_to_end_id`, exception type, evidence, screening disposition, proposed repair |
| `payment-failure-diagnoser` / `iso-20022-message-interpreter` | Diagnosed cause + the invalid/missing message field feeding the proposed repair |

## Downstream / lateral (route instead of acting)

| Skill | When |
| ----- | ---- |
| `payment-fraud-case-investigator` | The payment shows fraud / account-takeover indicators, not a data repair |
| `settlement-break-reconciler` | The break is a settlement-file / cash-ledger reconciliation item |
| `transaction-reconciliation-helper` | The break is a transaction-level processor/gateway/ledger mismatch |
| `dispute-operations-assistant` | The matter is a card dispute / chargeback, not a payment repair |
| Sanctions / compliance (human) | Screening is an uncleared hit or a pending disposition — this skill never adjudicates screening |
| Higher approver / policy-exception process (human) | Repair is out-of-catalog, over-limit, or irreversible |

## Duplicate-execution prevention

- Only this skill resubmits, releases, or returns the payment; upstream diagnosis and
  investigation skills must not submit.
- Execution is keyed by `plan_id` + step idempotency keys, each bound to the payment's
  **end-to-end id** — re-invocation never resubmits the same payment twice.
- If another workflow already resolved the payment (resubmitted, returned, or no longer
  held), the precondition check fails and this skill halts rather than re-applying.
