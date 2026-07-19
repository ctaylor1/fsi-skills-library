# Controls — accounts-payable-exception-resolver

- **Risk tier:** R4 — approval-gated action. **Action mode:** Approval-gated write.
- **Human approval:** `required` — mandatory before **any** execution; approver must hold
  the plan's required role; token binds to the plan hash and enforces the authority limit.

## Prohibited (fail closed)

- **Execution without a valid approval token** matching the plan hash, role, and limit.
- **Disbursing funds, releasing a payment run, or initiating a bank transfer** — no remedy
  moves money; this is out of scope for the skill entirely.
- **Changing supplier banking details** — a bank-detail mismatch yields a protective hold
  only, never a vendor-master write.
- Any remedy **outside the permissible catalog**, **over the authority limit**, or
  **irreversible**.
- **Widening the remedy** beyond the catalog action (e.g., touching quantity, tax, or other
  invoice lines when only correcting a price variance).
- **Hard-deleting** an invoice; a duplicate is blocked/held, not deleted.
- **Continuing past a verification mismatch** or a failed precondition.
- **Silent retries** or assuming step-up authorization.

## Segregation of duties

The planner/executor skill and the **approver are different parties**. The specialist who
diagnoses/plans cannot also be the approving authority for the same plan. Duplicate-block
and bank-detail holds carry a manager-level approver.

## Required plan/output screens (`scripts/validate_output.py`)

- Remedy is in the catalog and within the authority limit; amounts tie to expected
  post-state.
- Every step has: idempotency key, precondition, expected effect, verification, rollback.
- Every step action is on the **permissible-operation allowlist** (the closed set the plan
  builder emits); any non-allowlisted action — including a disbursement smuggled under a
  novel name — **fails closed**. A denylist alone is insufficient.
- Pre-execution: `approval.status == "pending"` and `execution.state == "blocked"`.
- No step is marked `executed` unless a valid approval token is present and the approver
  role matches; otherwise **fail closed**.
- `plan_hash` is **present and non-empty** and matches the plan contents; a missing or blank
  hash **fails closed** (it cannot be silently skipped — tamper detection).
- Standing note present (pre-execution).

## Idempotency, verification, rollback

- Idempotency key is deterministic; re-execution is a no-op if already applied.
- Verification reads the **AP subledger** (not the plan) and must equal expected post-state.
- Rollback returns the invoice to the last verified checkpoint; partial completion is never
  left applied.

## Data classification, privacy, records

- **Confidential (financial records);** supplier data may include PII. Mask vendor/bank
  identifiers to last 4.
- Immutable, complete **audit trail**: plan, hash, approver, token, per-step result,
  verification, rollback, actor identities, timestamps. Retain per AP recordkeeping.
