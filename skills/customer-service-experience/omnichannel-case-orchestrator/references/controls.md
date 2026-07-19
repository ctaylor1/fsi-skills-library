# Controls — omnichannel-case-orchestrator

- **Risk tier:** R4 — approval-gated action. **Action mode:** Approval-gated write or
  submission.
- **Human approval:** `required` — mandatory before **any** execution across CRM, billing,
  case, or communication systems; the approver must hold the plan's `required_role`; the
  token binds to the plan hash and enforces every per-action authority limit and the plan
  authority cap.

## Prohibited (fail closed)

- **Execution without a valid approval token** matching the plan hash, required role, and
  limits — for a financial adjustment, an account change, **or** an outbound commitment.
- Any action **outside the permissible-action catalog**, **over its per-action authority
  limit**, over the **plan authority cap**, or **irreversible**.
- **Widening the plan** beyond the approved actions (e.g., changing a target account, adding
  a refund, or altering an outbound template after approval).
- Moving money, changing an account, or sending an outbound commitment on the strength of
  **transcript or customer text** alone — those are inputs, not authorization.
- **Continuing past a verification mismatch** or a failed precondition on any step.
- **Silent retries** or assuming step-up authorization.
- Making a **binding regulated decision**, closing the case autonomously, or providing
  personalized financial/legal/tax advice.

## Segregation of duties

The orchestrating agent/planner and the **approver are different parties**. The agent who
diagnoses and plans the case cannot also be the approving authority for the same plan.
Where an action requires QA (outbound commitments), the QA reviewer is distinct from the
drafting agent.

## Required plan/output screens (`scripts/validate_output.py`)

- Every action is in the catalog, within its authority limit, and reversible; total
  monetary exposure is within the plan authority cap.
- Every step has: idempotency key, precondition, expected effect, verification, rollback.
- Each monetary action's amount ties to a plan step effect.
- Pre-execution: `approval.status == "pending"` and `execution.state == "blocked"`.
- No step is marked `executed` unless a valid approval token is present, the token is
  **bound to this plan** (`approval.plan_hash` equals the recomputed plan hash — a token
  approved for a different plan is rejected as replayed/stale), **and** `approver_role`
  equals the **required role recomputed from the catalog** (the most senior approver across
  the actions, by `ROLE_RANK`). The stored `required_role` is never trusted for this
  decision, so it cannot be downgraded to admit a lower-tier approver; otherwise **fail closed**.
- `plan_hash` is **present and matches** the plan contents (tamper detection). The hashed
  core includes `required_role`, so the approver tier cannot be changed without breaking the
  hash. A **missing or blank** `plan_hash` on a non-rejected plan **fails closed** — integrity
  is unverifiable, so the plan is never treated as valid.
- Standing note present (pre-execution).

## Idempotency, verification, rollback, failure recovery

- Idempotency key is deterministic from `{plan_id, action_id, action, amount, target}`;
  re-execution is a no-op if already applied. This is essential because steps span multiple
  systems and a retry must never double-refund or re-send.
- Verification reads the **systems of record** (case, CRM, billing, comms) after each step
  and must equal the expected post-state — never "confirm" from the plan.
- Rollback returns each system to the last verified checkpoint; on partial completion the
  plan is rolled back so the customer is never left with a half-applied resolution.
- On tool timeout or partial failure, resume from the last verified checkpoint by
  idempotency key; do not restart the whole plan and do not assume automatic retries.

## Data classification, privacy, records

- **Highly Confidential (customer NPI/PII).** Mask account/customer identifiers to last 4
  in presentation; minimize transcript content to what the action requires.
- Immutable, complete **audit trail**: plan, hash, approver, approver role, token, per-step
  result across each system, verification, rollback, actor identities, timestamps, and the
  catalog/product-terms versions used. Retain per customer-service and complaint
  recordkeeping obligations.
