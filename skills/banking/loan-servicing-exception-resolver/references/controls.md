# Controls — loan-servicing-exception-resolver

- **Risk tier:** R4 — approval-gated action. **Action mode:** Approval-gated write.
- **Human approval:** `required` — mandatory before **any** execution; approver must hold
  the plan's required role; token binds to the plan hash and enforces the authority limit.

## Prohibited (fail closed)

- **Execution without a valid approval token** matching the plan hash, role, and limit.
- Any remedy **outside the permissible catalog**, **over the authority limit**, or
  **irreversible**.
- **Widening the remedy** beyond the catalog action (e.g., touching principal/interest/other
  periods when only reallocating a payment).
- **Continuing past a verification mismatch** or a failed precondition.
- **Silent retries** or assuming step-up authorization.

## Segregation of duties

The planner/executor skill and the **approver are different parties**. The specialist who
diagnoses/plans cannot also be the approving authority for the same plan.

## Required plan/output screens (`scripts/validate_output.py`)

- Remedy is in the catalog and within the authority limit; amounts tie to expected
  post-state.
- Every step has: idempotency key, precondition, expected effect, verification, rollback.
- Pre-execution: `approval.status == "pending"` and `execution.state == "blocked"`.
- No step is marked `executed` unless a valid approval token is present and the approver
  role matches; otherwise **fail closed**.
- Standing note present (pre-execution).

## Idempotency, verification, rollback

- Idempotency key is deterministic; re-execution is a no-op if already applied.
- Verification reads the **system of record** (not the plan) and must equal expected
  post-state.
- Rollback returns the loan to the last verified checkpoint; partial completion is never
  left applied.

## Data classification, privacy, records

- **Highly Confidential (customer NPI/PII).** Mask loan/account identifiers to last 4.
- Immutable, complete **audit trail**: plan, hash, approver, token, per-step result,
  verification, rollback, actor identities, timestamps. Retain per servicing recordkeeping.
