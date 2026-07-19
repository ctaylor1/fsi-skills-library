# Controls — payment-repair-assistant

- **Risk tier:** R4 — approval-gated action. **Action mode:** Approval-gated write or
  submission.
- **Human approval:** `required` — mandatory before **any** execution (resubmit, release,
  return, cancel); approver must hold the plan's required role; token binds to the plan hash
  and enforces the authority limit.

## Prohibited (fail closed)

- **Execution without a valid approval token** matching the plan hash, role, and limit.
- **Resubmitting or releasing a payment whose sanctions screening is not cleared** (an
  uncleared hit or a pending disposition).
- Any repair **outside the permissible catalog**, **over the authority limit**, or
  **irreversible**.
- **Widening the repair** beyond the catalog action (e.g., changing amount, debtor, or value
  date when only correcting a beneficiary field).
- **Continuing past a verification mismatch** or a failed precondition, or acting when a
  duplicate submission cannot be ruled out.
- **Silent retries** or assuming step-up authorization — the fastest way to double-pay.

## Segregation of duties

The planner/executor skill and the **approver are different parties**. The specialist who
plans the repair cannot also be the approving authority for the same plan. Screening
disposition is owned by sanctions/compliance, not by this skill.

## Required plan/output screens (`scripts/validate_output.py`)

- Repair is in the catalog and within the authority limit; reversible; amounts tie to the
  repair amount.
- Sanctions screening is cleared for any resubmission/release.
- Every step has: idempotency key, precondition, expected effect, verification, rollback.
- Every payment-movement step (resubmit/return) is bound to the payment's **end-to-end id**
  (duplicate-payment guard).
- **`plan_hash` is present, non-empty, and matches the recomputed plan contents** (tamper
  detection). A non-rejected plan with a missing or blank hash **fails closed** — the check is
  never skipped, so content cannot be tampered and the hash dropped to evade detection.
- Pre-execution: `approval.status == "pending"` and `execution.state == "blocked"`.
- No step is marked `executed` unless a valid approval token is present and the approver role
  matches; otherwise **fail closed**.
- Standing note present (pre-execution).

## Idempotency, verification, rollback

- Idempotency key is deterministic and bound to the end-to-end id; re-execution of a movement
  step is a no-op if the payment already resubmitted/returned.
- Verification reads the **payment-operations system** (not the plan) and confirms the actual
  status and that **exactly one** submission/return occurred.
- Rollback returns the payment to the last verified checkpoint (recall/return via camt.056,
  re-hold, or restore the original field); a partial completion is never left applied.

## Data classification, privacy, records

- **Highly Confidential (customer NPI/PII; cardholder data).** Mask
  payment/account/beneficiary identifiers to last 4.
- Immutable, complete **audit trail**: plan, hash, screening disposition, approver, token,
  per-step result, verification, rollback, actor identities, timestamps. Retain per payments
  recordkeeping.
