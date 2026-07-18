# Domain Rules — loan-servicing-exception-resolver

The firm's servicing policy and its **permissible-remedy catalog** (versioned) govern.
Nothing outside the catalog may be planned or executed by this skill.

## Permissible-remedy catalog (default)

| Exception type | Remedy action | Evidence required | Reversible? | Authority limit | Approver role |
| -------------- | ------------- | ----------------- | ----------- | --------------- | ------------- |
| `misapplied_payment` | `reallocate_payment` (suspense → correct loan/bucket) | Payment record + correct allocation | Yes (reverse allocation) | ≤ 25,000 | servicing-supervisor |
| `late_fee_in_error` | `reverse_fee` (waive/reverse fee charged in error) | Fee record + error evidence | Yes (re-assess fee) | ≤ 500 | servicing-specialist |
| `escrow_shortage_miscalc` | `adjust_escrow` (correct escrow balance to recomputed value) | Escrow analysis + recomputation | Yes (restore prior balance) | ≤ 5,000 | escrow-analyst |
| `duplicate_payment` | `refund_duplicate` (return the duplicate payment) | Both payment records + duplication proof | Yes (reclaim/void refund) | ≤ 25,000 | servicing-supervisor |

Remedies not listed, over the authority limit, irreversible, or requiring a policy
exception are **out of scope** — fail closed and escalate to a human authority.

## Plan requirements (every step)

- **Idempotency key** deterministic from `{plan_id, step_id, remedy, amount, target}`;
  re-running a step with the same key must be a no-op.
- **Precondition** read from the servicing system (e.g., "suspense holds the payment",
  "fee still assessed") — checked at execute time, not assumed.
- **Expected effect** with amounts that tie to the remedy amount.
- **Verification** that reads the system of record after the step and compares to expected.
- **Rollback** method that returns the loan to the last verified state.

## Approval binding

- Approval yields a **token** bound to the **plan hash** and the approver's **role**.
- Any change to the plan after approval changes the hash and **voids** the token.
- Execution is permitted **only** with a valid token whose role matches the plan's required
  approver role and whose amount is within the authority limit.

## Post-state verification & rollback

- Verify the **actual** post-state (read the servicing system) equals the expected
  post-state. On mismatch, **roll back** the step and halt; never continue on a mismatch.
- On partial completion, roll back to the last verified checkpoint so the loan is never left
  half-corrected.
