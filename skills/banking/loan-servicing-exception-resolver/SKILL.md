---
name: loan-servicing-exception-resolver
description: >-
  Investigate a loan-servicing exception (misapplied payment, fee assessed in error, escrow
  miscalculation, duplicate payment), identify the root cause and the permissible remedy,
  and stage a validated correction plan for authorized approval and execution. Use when a
  loan operations or servicing specialist needs to resolve a servicing exception end to end
  with a controlled plan → validate → approve → execute → verify → audit workflow. This
  skill produces and, only AFTER explicit human approval, executes an idempotent correction
  with verification and rollback; it never posts, reverses, refunds, or changes a system of
  record without that approval.
license: MIT
compatibility: Amazon Quick Desktop; requires core-banking/loan-servicing, document-intelligence, approved-calculation, and permission/approval-broker MCP integrations. Read-only for planning; the execute operation is approval-gated and idempotent.
metadata:
  aws-fsi-category: "Banking"
  aws-fsi-skill-type: "Workflow or orchestration skills"
  aws-fsi-risk-tier: "R4"
  aws-fsi-archetype: "Orchestrate & resolve"
  aws-fsi-agent-pattern: "Plan-validate-execute workflow agent"
  aws-fsi-delivery-wave: "Wave 4 — gated orchestration"
  aws-fsi-action-mode: "Approval-gated write or submission"
  aws-fsi-scheduled-agent: "no"
  aws-fsi-baseline-status: "new"
  aws-fsi-human-approval: "required"
  aws-fsi-data-classification: "Highly Confidential (customer NPI/PII)"
  aws-fsi-jurisdictions: "US (default); configure additional jurisdiction packs per deployment"
  aws-fsi-owner: "Loan servicing operations / servicing controls"
  aws-fsi-primary-user: "Loan operations / servicing specialist"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-07-17"
---

# Loan Servicing Exception Resolver

## Purpose and outcome
Resolve a servicing exception through a controlled workflow: diagnose the root cause,
select a **permissible** remedy from the approved catalog, build a **validated correction
plan** (idempotent steps, preconditions, expected post-state, verification, rollback), and
— **only after explicit human approval** — execute it and verify the result, leaving a
complete audit trail. The outcome is a corrected loan record with evidence that every
change was authorized, verified, and reversible.

## Use when
- "Resolve this misapplied payment / this fee charged in error / this escrow miscalc /
  this duplicate payment."
- "Build the correction plan for servicing exception X and route it for approval."
- "Execute the approved correction and verify it posted."

## Do not use
- **Diagnosis only** with no correction intent → use `loan-servicing` analysis or
  `bank-statement-analyzer`; this skill is for staged, gated resolution.
- **Underwriting/closing completeness** → `loan-package-completeness-checker`.
- **Collections treatment** → `collections-treatment-planner`.
- **Accounts-payable / GL exceptions** → `accounts-payable-exception-resolver` / `gl-reconciler`.
- Any remedy **not in the permissible catalog**, over the monetary authority limit, or
  requiring a policy exception → stop and escalate to a human authority; do not improvise.

## Adjacent-skill handoffs
See [references/handoffs.md](references/handoffs.md). Upstream diagnosis skills may hand a
confirmed exception here with a durable `exception_id`; this skill owns the plan→execute
lifecycle and emits a `plan_id` + audit record. It never duplicates diagnosis-only or
GL/AP resolution work.

## Inputs and prerequisites
- A confirmed exception: `exception_id`, `loan_id`, type, evidence, and a proposed remedy
  (action, amount, target). Schema: [scripts/validate_input.py](scripts/validate_input.py).
- The **permissible-remedy catalog** and monetary authority limits (versioned).
- Read access for planning; the approval-gated **execute** operation and an approver with
  the required role. See [references/controls.md](references/controls.md).

## Source hierarchy
See [references/source-map.md](references/source-map.md). Loan-servicing is the system of
record; document-intelligence supplies evidence; the calculation service computes remedy
amounts and expected post-state. The remedy catalog and limits are versioned contracts.

## Workflow (plan → validate → approve → execute → verify → audit)
1. **Diagnose** — confirm the exception, root cause, and evidence; run `validate_input`.
2. **Select remedy** — match to the permissible-remedy catalog; confirm it is within the
   monetary authority limit and its evidence requirements are met. If not → fail closed and
   escalate.
3. **Plan (deterministic)** — run
   [scripts/calculate_or_transform.py](scripts/calculate_or_transform.py) to build the
   correction plan: ordered steps each with an **idempotency key**, precondition, expected
   effect, **verification** check, and **rollback**; plus the expected post-state and the
   required approver role. The plan starts `approval: pending`, `execution: blocked`.
4. **Validate the plan** — run [scripts/validate_output.py](scripts/validate_output.py):
   amounts tie, remedy is permissible/in-limit, every step is idempotent + verifiable +
   reversible, and execution is blocked pending approval. Fail closed on any miss.
5. **Approve** — present the plan for human approval. Approval supplies an **approval
   token** bound to the plan hash and the approver's role. No token, no execution.
6. **Execute** — only with a valid token: run each step **idempotently** (re-running a step
   with the same idempotency key must not double-apply). Stop on the first failed
   precondition/verification.
7. **Verify** — confirm the actual post-state equals the expected post-state; if not, invoke
   **rollback** and report.
8. **Audit** — record plan, approver, token, each step result, verification, and any
   rollback.

## Validation loop
`validate_input` before planning; `validate_output` after planning **and** before execution
(re-check the plan is still blocked/pending and unchanged). After execution, verify
post-state; on mismatch, roll back and fail closed. Never assume automatic retries.

## Human approval
`required` — **mandatory before any execution**. The approver must hold the role named in
the plan; the approval token binds to the exact plan (hash) so an altered plan invalidates
the approval. Monetary authority limits are enforced; over-limit remedies require a higher
approver and are out of scope for auto-planning.

## Failure handling
- **Remedy not permissible / over limit / missing evidence** → fail closed; escalate; no plan
  executes.
- **Precondition fails at execute** → stop; do not force; report the blocking state.
- **Verification mismatch after a step** → **roll back** that step and halt; report.
- **Partial completion / tool timeout** → leave the loan in a consistent state (rolled back
  to last verified checkpoint); never leave a half-applied correction; no silent retry.
- **Altered plan / stale token** → refuse to execute; re-plan and re-approve.

## Output contract
1. **Plan** — `plan_id`, exception/loan, remedy, amount, ordered steps (idempotency key,
   precondition, expected effect, verification, rollback), expected post-state, required
   approver role, `approval: pending`, `execution: blocked`.
2. **Validation result** — plan checks passed/failed.
3. **Execution record** (post-approval) — token, per-step result, verification, rollback if any.
4. **Audit trail** — actor, approver, timestamps, before/after state, citations.
5. **Standing note** — "Plan only; no system-of-record change has been executed. Execution
   requires human approval." (before execution).
See [references/controls.md](references/controls.md).

## Privacy and records
Customer NPI/PII. Mask loan/account identifiers to last 4 in presentation. Retain plan,
approval, execution, verification, and rollback records per servicing recordkeeping; the
audit trail is immutable and complete. Log actor and approver identities.

## Gotchas
- **Approval binds to the plan, not the exception.** Editing the plan after approval voids
  the token — re-approve.
- **Idempotency is mandatory.** A retried step must be a no-op if already applied; use the
  idempotency key, never assume "it probably didn't post."
- **Reversibility first.** If a remedy step cannot be rolled back, it needs a higher control
  and is out of scope for auto-planning.
- **Verify against the record, not the plan.** Post-state verification reads the servicing
  system; do not "confirm" from the plan you just wrote.
- **Never widen the remedy.** Fixing a misapplied payment does not authorize touching
  interest, principal, or other periods unless the catalog remedy explicitly includes them.
