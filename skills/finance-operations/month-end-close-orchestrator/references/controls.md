# Controls — month-end-close-orchestrator

- **Risk tier:** R4 — approval-gated action. **Action mode:** Approval-gated write or submission.
- **Human approval:** `required` — mandatory before **any** posting, certification, or lock;
  the approver must hold the plan's required role; the token binds to the plan hash and
  enforces the posting-authority limit.

## Prohibited (fail closed)

- **Execution without a valid approval token** matching the plan hash, role, and limit.
- Any action **outside the permissible close-action catalog**, a journal **over its
  posting-authority limit**, or any action that is **irreversible**.
- **Certifying a reconciliation with unresolved breaks**, or certifying a task whose
  prerequisites are not complete (dependency-order violation).
- **Locking a sub-ledger or closing the period** before its prerequisite steps are verified.
- **Continuing past a verification mismatch** or a failed precondition.
- **Silent retries** or assuming step-up authorization.

## Segregation of duties

The planner/executor skill and the **approver are different parties**. The preparer who
builds the plan cannot also be the approving authority for the same plan. Journal preparation
is segregated from journal approval, and reconciliation preparation from its certification.

## Required plan/output screens (`scripts/validate_output.py`)

- Every step action is a permissible catalog action; journals are within the
  posting-authority limit and the effect amount ties to the posted delta.
- Every step has: idempotency key, precondition, expected effect, verification, rollback.
- Every `certify_reconciliation` step carries a zero-breaks attestation
  (`unresolved_breaks == 0`); a certify step with a missing or non-zero `unresolved_breaks`
  is **rejected** — a reconciliation is never certified while it still has unresolved breaks.
- Dependency order is valid: each step's prerequisites are sequenced earlier, and no executed
  step skipped an unexecuted prerequisite.
- `plan_hash` is present **and** matches the plan contents; a missing/empty hash **fails
  closed** — dropping the field must not skip tamper detection and let a post-approval edit pass.
- Pre-execution: `approval.status == "pending"` and `execution.state == "blocked"`.
- No step is marked `executed` unless a valid approval token is present, the approver is
  recorded, and the role matches; otherwise **fail closed**.
- Standing note present (pre-execution).

## Idempotency, verification, rollback

- Each step's idempotency key is deterministic; re-execution is a no-op if already applied.
- Verification reads the **system of record** (GL, close-task system, period-control system)
  — never the plan — and must equal the expected post-state.
- Rollback returns the close to the last verified checkpoint: reverse a journal, rescind a
  certification, or re-open a locked sub-ledger/period. Partial completion is never left
  applied; the period is never left half-closed.

## Data classification, privacy, records

- **Confidential (financial records).** Restrict to close/controllership personnel; apply
  least privilege to GL and sub-ledger access.
- Immutable, complete **audit trail**: plan, hash, approver, token, per-step result,
  verification, rollback, actor identities, timestamps. Retain per the entity's financial
  recordkeeping and SOX evidence policy so the close is reproducible for internal and
  external audit.
