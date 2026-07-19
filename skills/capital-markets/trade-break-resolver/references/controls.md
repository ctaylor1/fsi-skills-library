# Controls — trade-break-resolver

- **Risk tier:** R4 — approval-gated action. **Action mode:** Approval-gated write.
- **Human approval:** `required` — mandatory before **any** execution; approver must hold the
  plan's required role; token binds to the plan hash and enforces the authority limit.

## Prohibited (fail closed)

- **Execution without a valid approval token** matching the plan hash, role, and limit.
- Any repair **outside the permissible catalog**, **over the authority limit**, or
  **irreversible**.
- **Writing the counterparty, custodian, or CCP record** — the firm repairs only its own
  OMS/EMS booking.
- **Widening the repair** beyond the catalog action (e.g., touching quantity, price, or
  settlement date when only rebooking a mis-booked account).
- **Continuing past a verification mismatch** or a failed precondition.
- **Silent retries** or assuming step-up authorization.

## Segregation of duties

The planner/executor skill and the **approver are different parties**. The analyst who
classifies/plans cannot also be the approving authority for the same plan.

## Required plan/output screens (`scripts/validate_output.py`)

- Repair is in the catalog and within the **catalog** authority limit for the break type;
  amounts tie to expected post-state. The limit is read from the same permissible-repair
  catalog the planning engine uses — the plan's own self-declared `authority_limit` is
  informational and can never raise the effective limit.
- Every step has: idempotency key, precondition, expected effect, verification, rollback.
- `plan_hash` is **present** and matches plan contents (tamper detection). A missing or blank
  hash on a non-rejected plan **fails closed** — an unhashable plan cannot be trusted for
  execution.
- Pre-execution: `approval.status == "pending"` and `execution.state == "blocked"`.
- No step is marked `executed` unless a valid approval token is present and the approver's role
  matches the **catalog-required** approver role for the break type; otherwise **fail closed**.
- Standing note present (pre-execution).

## Idempotency, verification, rollback

- Idempotency key is deterministic; re-execution is a no-op if already applied.
- Verification reads the **system of record** (OMS/EMS), not the plan, and must equal expected
  post-state.
- Rollback returns the trade to the last verified checkpoint; partial completion is never left
  applied.

## Data classification, privacy, records

- **Highly Confidential (customer NPI/PII)** and market-sensitive trade data. Mask account /
  trade identifiers to last 4.
- Immutable, complete **audit trail**: plan, hash, approver, token, per-step result,
  verification, rollback, actor identities, timestamps. Retain per books-and-records
  requirements.
