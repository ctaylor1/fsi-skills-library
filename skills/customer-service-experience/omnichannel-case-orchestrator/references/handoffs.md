# Adjacent-Skill Handoffs — omnichannel-case-orchestrator

This skill owns the **plan → validate → approve → execute → verify → audit** lifecycle for a
confirmed service case: it unifies cross-channel history and coordinates the agreed
resolution actions (financial adjustments, account changes, outbound commitments). It does
not diagnose-only, compose knowledge answers, or resolve product-specific exceptions that
belong to a specialist skill.

## Upstream (hand a confirmed case + proposed actions here)

| Upstream source | Handoff artifact |
| --------------- | ---------------- |
| `customer-interaction-summarizer` | Unified cross-channel interaction summary + `case_id` |
| `complaint-resolution-assistant` | Drafted resolution with proposed remedies to be executed |
| `next-best-action-assistant` | Recommended next action(s) for the case |
| `service-recovery-assistant` | Proposed goodwill / service-recovery gesture |
| `knowledge-answer-composer` | Approved answer / eligibility grounding for an action |

Upstream skills confirm and propose; only this skill stages a gated, idempotent plan and —
after approval — executes it and emits a `plan_id` + audit record.

## Downstream / lateral (route instead of acting)

| Skill | When |
| ----- | ---- |
| `dispute-operations-assistant` | The matter is a card/transaction dispute, not a case remedy |
| `chargeback-dispute-packager` | A chargeback needs to be packaged and represented |
| `payment-exception-investigator` | A payment exception needs investigation before any repair |
| `payment-repair-assistant` | A payment must be repaired/reprocessed (payment-rail action) |
| `loan-servicing-exception-resolver` | The correction is a loan-servicing exception (misapplied payment, escrow, fee) |
| `fee-and-charge-reviewer` | A fee's correctness must be reviewed before deciding to adjust it |
| `kyc-customer-due-diligence-screener` | An account change needs identity / due-diligence re-verification first |
| `vulnerable-customer-support-assistant` | The customer shows vulnerability signals needing specialized handling |
| `call-quality-compliance-reviewer` | The interaction needs a QA / conduct review rather than a resolution action |
| Human authority / policy-exception process | Any action is out-of-catalog, over-limit, over the plan cap, or irreversible |

## Duplicate-execution prevention

- Only this skill executes the coordinated actions; upstream diagnosis/drafting skills must
  not also post, refund, change an account, or send an outbound commitment.
- Execution is keyed by `plan_id` + step idempotency keys — re-invocation never
  double-applies (no double refund, no duplicate confirmation sent).
- If another workflow already resolved part of the case, the affected step's precondition
  fails and this skill halts on that step rather than re-applying.
