# Controls — employee-trading-preclearance-assistant

- **Risk tier:** R4 — approval-gated action. **Action mode:** Approval-gated write or submission.
- **Human approval:** `required` — mandatory before **any** decision is recorded or any
  clearance is issued; the approver must hold the plan's required role; the token binds to
  the plan hash and enforces the notional authority limit.

## Prohibited (fail closed)

- **Recording a decision or issuing a clearance without a valid approval token** matching the
  plan hash, role, and limit.
- **Auto-approving a hard-blocked request.** Any hard block — restricted-list hit, active
  blackout, minimum-holding breach, or a conflict/MNPI flag — permits only a `deny` decision.
  An `approve*` plan for a hard-blocked request is impermissible and must fail closed.
- **Clearing above the authority limit.** Notional over the senior limit is out of scope for
  auto-planning and escalates to the Chief Compliance Officer (CCO).
- **Issuing a clearance on a `deny` decision**, or widening a clearance beyond the requested
  instrument, side, and notional.
- **Providing personalized investment advice** or opining on whether a trade is a good idea.
- **Continuing past a verification mismatch**, a failed precondition, silent retries, or
  assumed step-up authorization.

## Segregation of duties

The requesting **employee and the approver are different parties**, and the approver holds
the required compliance role. An employee can never pre-clear their own trade; the analyst
who assembles the plan cannot be the approving authority for a request they submitted.

## Required plan/output screens (`scripts/validate_output.py`)

- Decision is one of `approve` / `approve_with_conditions` / `deny`; approve* is blocked when
  any hard block is present; required approver role matches the decision.
- Notional is within the decision's authority limit; the clearance step ties to the exact
  plan notional; a `deny` plan issues no clearance.
- Every step has: idempotency key, precondition, expected effect, verification, rollback, and
  a post-state contribution.
- Pre-execution: `approval.status == "pending"` and `execution.state == "blocked"`; standing
  note present.
- No step is marked `executed` unless a valid approval token is present, the approver role
  matches, and the approver is not the requesting employee; otherwise **fail closed**.

## Idempotency, verification, rollback

- Idempotency key is deterministic from `{plan_id, step_id, action, post_state}`; re-execution
  is a no-op if already applied.
- Verification reads the **preclearance register** (not the plan) and must equal the expected
  post-state (decision recorded, clearance window active, conditions applied).
- Rollback voids the recorded decision, revokes the clearance window, or removes conditions,
  returning the request to the last verified checkpoint. Audit entries are append-only;
  reversals are recorded as compensating annotations.

## Data classification, privacy, records

- **Restricted (AML/BSA — SAR confidentiality; tipping-off controls).** Employee personal-
  trading data and MNPI are highly sensitive; mask employee/account identifiers to last 4 and
  restrict MNPI details to entitled reviewers.
- Immutable, complete **audit trail**: plan, hash, screens relied on (with versions),
  approver, token, per-step result, verification, rollback, actor identities, timestamps.
  Retain per the personal-trading recordkeeping schedule and the records archive.
