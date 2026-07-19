---
name: month-end-close-orchestrator
description: >-
  Orchestrate a month-end (or period-end) close: coordinate close tasks and their
  dependencies, and build a validated, idempotent plan that gates every posting and sign-off
  — accrual/reclass/allocation journals, reconciliation and task certifications, sub-ledger
  and period locks. Use when a controller, close manager, or accountant needs to run the
  close end to end with a controlled plan → validate → approve → execute → verify → audit
  workflow, sequencing dependent tasks and staging postings for authorized execution. This
  skill produces and, only AFTER a valid human approval token bound to the plan, executes
  idempotent steps with verification and rollback; it NEVER posts a journal, certifies a
  reconciliation or task, locks a sub-ledger, or closes a period without that approval, and
  never certifies a reconciliation that still has unresolved breaks.
license: MIT
compatibility: Amazon Quick Desktop; requires ERP/general-ledger, subledger, close-task/certification, reconciliation, and permission/approval-broker MCP integrations, plus document/spreadsheet intelligence. Read-only for planning; posting, certification, and lock operations are approval-gated and idempotent.
metadata:
  aws-fsi-category: "Finance & Operations"
  aws-fsi-skill-type: "Workflow or orchestration skills"
  aws-fsi-risk-tier: "R4"
  aws-fsi-archetype: "Orchestrate & resolve"
  aws-fsi-agent-pattern: "Plan-validate-execute workflow agent"
  aws-fsi-delivery-wave: "Wave 4 - gated orchestration"
  aws-fsi-action-mode: "Approval-gated write or submission"
  aws-fsi-scheduled-agent: "no"
  aws-fsi-baseline-status: "new"
  aws-fsi-human-approval: "required"
  aws-fsi-data-classification: "Confidential (financial records)"
  aws-fsi-jurisdictions: "US (default); configure additional jurisdiction packs per deployment"
  aws-fsi-owner: "Finance & Controllership"
  aws-fsi-primary-user: "Controller / close manager / accountant"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-07-17"
---

# Month-End Close Orchestrator

## Purpose and outcome
Run a period-end close through a controlled workflow: read the close-task graph, order tasks
by their dependencies, and build a **validated close-execution plan** whose steps each carry
an idempotency key, a precondition, an expected effect, a verification read, and a rollback —
plus an expected post-state and a plan hash. Then, **only after explicit human approval**,
execute the postings, certifications, and locks idempotently, verify each against the system
of record, and leave a complete audit trail. The outcome is a closed period with evidence
that every journal, sign-off, and lock was authorized, verified, and reversible.

## Use when
- "Build the close plan for this period: post the accruals, certify the reconciliations, then
  lock the sub-ledgers and close the period — and route it for approval."
- "Sequence these close tasks by their dependencies and stage the postings for sign-off."
- "Execute the approved close plan and verify each posting and certification landed."

## Do not use
- **Clearing reconciliation breaks** → route to `gl-reconciler` or
  `transaction-reconciliation-helper`; this skill certifies a reconciliation only when its
  breaks are already zero.
- **Resolving a sub-ledger exception** (e.g., duplicate/misapplied AP payment) →
  `accounts-payable-exception-resolver`.
- **Post-close variance / flux analysis** → `fpa-variance-analyzer`.
- **Assembling the reporting or audit package** → `management-reporting-packager`,
  `audit-evidence-packager`, or `financial-statement-audit-assistant`.
- Any action **not in the permissible close-action catalog**, a journal **over its
  posting-authority limit**, or an **irreversible** action → stop and escalate to a human
  authority; do not improvise.

## Adjacent-skill handoffs
See [references/handoffs.md](references/handoffs.md). Upstream reconciliation and exception
skills must deliver clean inputs (zero unresolved breaks, resolved exceptions) before a step
can be certified or a ledger locked; this skill owns the plan→execute lifecycle and emits a
`plan_id` + audit record. Downstream packaging, variance, and audit-evidence skills consume
the closed period. It never duplicates reconciliation, exception-resolution, or reporting work.

## Inputs and prerequisites
- A close-run request: `close_run_id`, `entity`, `period`, `catalog_version`, and `tasks[]`
  where each task has `task_id`, `action`, `target`, `depends_on[]`, `evidence{}`, and (for
  journals) `amount`. Schema: [scripts/validate_input.py](scripts/validate_input.py).
- The **permissible close-action catalog** and posting-authority limits (versioned).
- Read access for planning; the approval-gated **execute** operations and an approver holding
  the plan's required role. See [references/controls.md](references/controls.md).

## Source hierarchy
See [references/source-map.md](references/source-map.md). The ERP/GL is the system of record
for balances and period state; the close-task/certification system is authoritative for the
task graph and sign-offs; the reconciliation platform supplies unresolved-break counts. The
close-action catalog and authority limits are versioned contracts. On conflict, the system of
record for the specific object wins and the discrepancy is surfaced, not silently reconciled.

## Workflow (plan → validate → approve → execute → verify → audit)
1. **Intake** — load the close-run request; run `validate_input`. Fail closed on an
   out-of-catalog action, an over-limit journal, missing evidence, an un-cleared
   reconciliation, a dangling/duplicate task id, or a dependency cycle.
2. **Order** — topologically sort the tasks by `depends_on` into an ordered set of steps
   (ties broken by task id for determinism). A cycle or dangling dependency is rejected.
3. **Plan (deterministic)** — run
   [scripts/calculate_or_transform.py](scripts/calculate_or_transform.py) to build the plan:
   each step has an **idempotency key**, precondition (state read + prerequisites), expected
   effect, **verification**, and **rollback**; plus the expected post-state, the plan hash,
   and the required approver role (the strictest across steps). The plan starts
   `approval: pending`, `execution: blocked`.
4. **Validate the plan** — run [scripts/validate_output.py](scripts/validate_output.py):
   actions are permissible/in-limit, journal amounts tie to posted deltas, every step is
   idempotent + verifiable + reversible, every `certify_reconciliation` step attests zero
   unresolved breaks, dependency order is valid, the plan hash is present and matches (a
   missing/empty hash fails closed), and execution is blocked pending approval. Fail closed on
   any miss.
5. **Approve** — present the plan for human approval. Approval supplies an **approval token**
   bound to the plan hash and the approver's role. No token, no execution.
6. **Execute** — only with a valid token: run each step **idempotently** in dependency order
   (re-running a step with the same idempotency key must not double-apply). Stop on the first
   failed precondition or verification.
7. **Verify** — confirm the actual post-state equals the expected post-state; if not, invoke
   **rollback** and report.
8. **Audit** — record plan, hash, approver, token, each step result, verification, and any
   rollback.

## Validation loop
`validate_input` before planning; `validate_output` after planning **and** before execution
(re-check the plan is still blocked/pending and unchanged). After each executed step, verify
the post-state against the system of record; on mismatch, roll back and fail closed. Never
assume automatic retries.

## Human approval
`required` — **mandatory before any posting, certification, or lock**. The approver must hold
the role named in the plan (`controller` for any journal, sub-ledger lock, or period close;
`close-manager` for certifications only). The approval token binds to the exact plan (hash)
so an altered plan invalidates the approval. Posting-authority limits are enforced;
over-limit journals require a higher approver and are out of scope for auto-planning.
Preparer and approver are different parties (segregation of duties).

## Failure handling
- **Out-of-catalog / over-limit / irreversible action, or un-cleared reconciliation** → fail
  closed; escalate or route upstream; no plan executes.
- **Dependency cycle or dangling dependency** → reject the run; no plan is built.
- **Precondition fails at execute** (period already locked, prerequisite not verified) → stop;
  do not force; report the blocking state.
- **Verification mismatch after a step** → **roll back** that step and halt; report.
- **Partial completion / tool timeout** → leave the close in a consistent state (rolled back
  to the last verified checkpoint); never leave the period half-closed; no silent retry.
- **Altered plan / stale token** → refuse to execute; re-plan and re-approve.

## Output contract
1. **Plan** — `plan_id`, close-run/entity/period, ordered steps (idempotency key, precondition,
   expected effect, verification, rollback, dependency links), expected post-state, plan hash,
   required approver role, `approval: pending`, `execution: blocked`.
2. **Validation result** — plan checks passed/failed.
3. **Execution record** (post-approval) — token, per-step result, verification, rollback if any.
4. **Audit trail** — actor, approver, timestamps, before/after state, citations.
5. **Standing note** — "Plan only; no journal has been posted and no task, reconciliation, or
   period has been certified or locked. Execution requires human approval." (before execution).
See [references/controls.md](references/controls.md).

## Privacy and records
Confidential financial records. Restrict to close/controllership personnel under least
privilege. Retain plan, approval, execution, verification, and rollback records per the
entity's financial recordkeeping and SOX evidence policy; the audit trail is immutable and
complete, and the close is reproducible for internal and external audit. Log actor and
approver identities.

## Gotchas
- **Approval binds to the plan, not the close.** Editing any step (e.g., a journal amount)
  after approval voids the token — re-approve.
- **Idempotency is mandatory.** A retried post must be a no-op if already applied; use the
  idempotency key, never assume "it probably didn't post."
- **Order is a control, not a convenience.** A sub-ledger lock or period close sequenced or
  executed before its prerequisites are verified is a control failure — `validate_output`
  rejects it.
- **Zero breaks before certifying.** A reconciliation with any unresolved break cannot be
  certified; route it to `gl-reconciler` first.
- **Verify against the record, not the plan.** Post-state verification reads the GL and
  close-task systems; do not "confirm" from the plan you just wrote.
- **Reversibility first.** If a close action cannot be rolled back, it needs a higher control
  and is out of scope for auto-planning.
