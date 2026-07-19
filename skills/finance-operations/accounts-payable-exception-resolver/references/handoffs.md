# Adjacent-Skill Handoffs — accounts-payable-exception-resolver

This skill owns the **plan → approve → execute → verify → audit** lifecycle for a confirmed
accounts-payable exception. It does not diagnose-only, reconcile the GL, orchestrate the
close, or disburse funds.

## Upstream (hands a confirmed exception here)

| Upstream source | Handoff artifact |
| --------------- | ---------------- |
| Invoice / three-way-match review that confirms an AP exception | `exception_id`, `invoice_id`, `vendor_id`, type, evidence, proposed remedy |
| `gl-reconciler` surfacing an AP break that is actually an invoice/PO/receipt exception | `exception_id` + evidence |
| `month-end-close-orchestrator` routing an AP correction needed before close | `exception_id` + due date |

## Downstream / lateral (route instead of acting)

| Skill | When |
| ----- | ---- |
| `gl-reconciler` | The break is a general-ledger reconciliation item, not an AP invoice exception |
| `month-end-close-orchestrator` | The work is period-close orchestration across the ledger |
| `loan-servicing-exception-resolver` | The exception is a loan-servicing issue, not AP |
| `audit-evidence-packager` | An auditor needs the correction packaged as evidence |
| `third-party-risk-assessor` | The bank-detail change needs supplier due diligence (this skill only holds the invoice) |
| Human authority / vendor-master control / treasury payment-run process | Remedy is out-of-catalog, over-limit, irreversible, a bank-master change, or a disbursement |

## Duplicate-execution prevention

- Only this skill executes the AP correction; upstream review skills must not also post.
- Execution is keyed by `plan_id` + step idempotency keys — re-invocation never double-applies.
- If another workflow already resolved the exception (invoice paid, hold lifted, PO closed),
  the precondition check fails and this skill halts rather than re-applying.
