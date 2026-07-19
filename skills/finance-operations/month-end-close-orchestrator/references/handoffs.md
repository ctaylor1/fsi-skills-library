# Adjacent-Skill Handoffs — month-end-close-orchestrator

This skill owns the **plan → validate → approve → execute → verify → audit** lifecycle for
the close: it coordinates tasks and dependencies and gates every posting, certification, and
lock. It does not clear reconciliation breaks, resolve sub-ledger exceptions, build reporting
packages, or perform variance analysis — those are separate skills it routes to.

## Upstream (must be clean before a step can be planned or certified)

| Upstream skill | Handoff artifact | Gate it satisfies |
| -------------- | ---------------- | ----------------- |
| `gl-reconciler` | Reconciliation with zero unresolved breaks + `reconciliation_ref` | `certify_reconciliation` requires `unresolved_breaks == 0` |
| `transaction-reconciliation-helper` | Cleared sub-ledger-to-GL reconciliation evidence | Sub-ledger tie-out before `lock_subledger` |
| `accounts-payable-exception-resolver` | Resolved AP exception (misapplied/duplicate payment) | AP sub-ledger ties before its lock |
| `financials-normalizer` | Normalized trial balance / mapped accounts | Clean inputs for accrual and allocation journals |

If an upstream gate is not satisfied (open breaks, unresolved exception), this skill **fails
closed** on that task and routes the item back to the upstream skill rather than certifying
or locking around it.

## Downstream / lateral (route instead of acting)

| Skill | When |
| ----- | ---- |
| `management-reporting-packager` | The period is closed and the reporting/board package is needed |
| `fpa-variance-analyzer` | Post-close variance / flux analysis of the closed numbers |
| `regulatory-reporting-data-validator` | Closed data must be validated for a regulatory filing |
| `audit-evidence-packager` | The close audit trail must be bundled as audit evidence |
| `financial-statement-audit-assistant` | An auditor needs support over the closed statements |
| Human authority / controllership | Out-of-catalog action, over-limit journal, irreversible step, or a policy exception |

## Duplicate-execution prevention

- Only this skill executes the gated close actions; upstream diagnosis/reconciliation skills
  must not also post, certify, or lock.
- Execution is keyed by `plan_id` + per-step idempotency keys — re-invocation never
  double-posts a journal or re-certifies a task.
- If another workflow already completed a step, the precondition check reads it as already
  applied and the step is a no-op rather than a second application.
