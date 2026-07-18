# Adjacent-Skill Handoffs — loan-servicing-exception-resolver

This skill owns the **plan → approve → execute → verify → audit** lifecycle for a confirmed
servicing exception. It does not diagnose-only, nor resolve GL/AP exceptions.

## Upstream (hands a confirmed exception here)

| Upstream source | Handoff artifact |
| --------------- | ---------------- |
| Servicing diagnosis / `bank-statement-analyzer` review that confirms an exception | `exception_id`, `loan_id`, type, evidence, proposed remedy |
| `covenant-compliance-monitor` / servicing queues surfacing a correctable exception | `exception_id` + evidence |

## Downstream / lateral (route instead of acting)

| Skill | When |
| ----- | ---- |
| `accounts-payable-exception-resolver` | The exception is an AP/vendor issue, not loan servicing |
| `gl-reconciler` | The break is a general-ledger reconciliation item |
| `collections-treatment-planner` | The matter is delinquency treatment, not a correction |
| `loan-package-completeness-checker` | Underwriting/closing package completeness |
| Human authority / policy-exception process | Remedy is out-of-catalog, over-limit, or irreversible |

## Duplicate-execution prevention

- Only this skill executes the correction; upstream diagnosis skills must not also post.
- Execution is keyed by `plan_id` + step idempotency keys — re-invocation never double-applies.
- If another workflow already resolved the exception, the precondition check fails and this
  skill halts rather than re-applying.
