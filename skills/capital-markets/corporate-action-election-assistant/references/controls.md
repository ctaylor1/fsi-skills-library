# Controls — corporate-action-election-assistant

- **Risk tier:** R4 — approval-gated action. **Action mode:** Approval-gated write or submission.
- **Human approval:** `required` — mandatory before **any** election submission; approver
  must hold the plan's required role; token binds to the plan hash and enforces the notional
  authority limit.

## Prohibited (fail closed)

- **Submission without a valid approval token** matching the plan hash, role, and limit.
- Any option **outside the permissible catalog**, an instructed quantity **over the eligible
  position** (or oversubscription cap), a notional **over the authority limit**, or an
  **irreversible** event.
- **Submitting past the agent/custodian cutoff** — the election window is closed; a
  late/protect instruction is a manual operations decision.
- **Recommending which option to elect** (investment advice) or opining on the **tax**
  outcome — out of scope; route to a licensed representative / tax professional.
- **Continuing past a verification mismatch** or a failed precondition.
- **Silent retries** or assuming step-up authorization.

## Segregation of duties

The planner/submitter skill and the **approver are different parties**. The specialist who
stages the election cannot also be the approving authority for the same plan.

## Required plan/output screens (`scripts/validate_output.py`)

- Election action is a catalog action; every leg option is permissible for the event type.
- Leg quantities tie to `instructed_quantity`; the instructed quantity does not over-elect
  the eligible position (entire-basis events allocate the whole position).
- Notional is within the authority limit and ties to instructed × reference price; the event
  is reversible before the deadline.
- The request is inside the submission window (`as_of` strictly before `submission_deadline`).
- The `plan_hash` is **present and matches** the plan contents; a missing or blank hash is a
  hard error (integrity cannot be verified, so **fail closed** — a removed hash never skips
  the tamper screen).
- Every step has: idempotency key, precondition, expected effect, verification, rollback.
- Pre-submission: `approval.status == "pending"` and `execution.state == "blocked"`.
- No step is marked submitted unless a valid approval token is present and the approver role
  matches; otherwise **fail closed**.
- Standing note present (pre-submission).

## Idempotency, verification, rollback

- Idempotency key is deterministic; re-submission of a leg is a no-op if already acknowledged.
- Verification reads the **custodian/agent acknowledgment** (not the plan) and must match the
  intended option and quantity.
- Rollback withdraws/supersedes a leg before the deadline; partial completion is never left
  as a half-submitted election.

## Data classification, privacy, records

- **Highly Confidential (customer NPI/PII).** Mask account identifiers to last 4.
- Immutable, complete **audit trail**: plan, hash, approver, token, per-leg submission
  result, acknowledgment, withdrawal, actor identities, timestamps. Retain per corporate-
  actions recordkeeping.
