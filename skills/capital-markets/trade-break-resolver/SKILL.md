---
name: trade-break-resolver
description: >-
  Investigate a trade break (a confirmed mismatch between the firm's booking and a
  counterparty, custodian, or clearing record — mis-booked account, quantity mismatch,
  price mismatch, or duplicate booking), classify it, identify the likely root cause, and
  stage a validated repair plan with full lineage for authorized approval and execution.
  Use when a middle-office or trade-support analyst needs to resolve a trade break end to
  end with a controlled plan → validate → approve → execute → verify → audit workflow. This
  skill produces and, only AFTER explicit human approval bound to the plan, executes an
  idempotent OMS/EMS repair with verification and rollback; it never amends, cancels,
  rebooks, or writes a system of record without that approval.
license: MIT
compatibility: Amazon Quick Desktop; requires OMS/EMS, post-trade/clearing, market & reference-data, communications-archive, and permission/approval-broker MCP integrations. Read-only for planning; the execute operation is approval-gated and idempotent.
metadata:
  aws-fsi-category: "Capital Markets"
  aws-fsi-skill-type: "Workflow or orchestration skills"
  aws-fsi-risk-tier: "R4"
  aws-fsi-archetype: "Orchestrate & resolve"
  aws-fsi-agent-pattern: "Plan-validate-execute workflow agent"
  aws-fsi-delivery-wave: "Wave 4 - gated orchestration"
  aws-fsi-action-mode: "Approval-gated write or submission"
  aws-fsi-scheduled-agent: "no"
  aws-fsi-baseline-status: "new"
  aws-fsi-human-approval: "required"
  aws-fsi-data-classification: "Highly Confidential (customer NPI/PII)"
  aws-fsi-jurisdictions: "US (default); configure additional jurisdiction packs per deployment"
  aws-fsi-owner: "Capital Markets operations & compliance"
  aws-fsi-primary-user: "Middle-office / trade-support analyst"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-07-17"
---

# Trade Break Resolver

## Purpose and outcome
Resolve a trade break through a controlled workflow: match the firm's booking against the
counterparty/custodian/clearing record, classify the break, diagnose the likely root cause,
select a **permissible** repair from the approved catalog, build a **validated repair plan**
(idempotent steps, preconditions, expected post-state, verification, rollback), and — **only
after explicit human approval** — execute it in the OMS/EMS and verify the result, leaving a
complete audit trail. The outcome is a corrected trade record with evidence that every change
was authorized, verified, and reversible.

## Use when
- "Resolve this trade break / this mis-booked trade / this quantity or price mismatch / this
  duplicate booking, and route the repair for approval."
- "Build the repair plan for trade break X and stage it for the desk supervisor."
- "Execute the approved repair and verify it booked to the correct desk/account."

## Do not use
- **Diagnosis / explanation only** with no repair intent → use `trade-confirmation-explainer`;
  this skill is for staged, gated resolution.
- **Settlement-fail monitoring / aging / cutoff triage** → `post-trade-settlement-monitor`.
- **Regulatory transaction-reporting completeness or re-reporting** →
  `transaction-reporting-quality-checker`.
- **Execution-quality / venue / routing review** → `best-execution-reviewer`.
- **Potential misconduct signal** (not an ops break) → `market-surveillance-alert-investigator`.
- **Unprocessed corporate action** masquerading as a break → `corporate-action-interpreter`.
- Any repair **not in the permissible catalog**, over the authority limit, or irreversible →
  stop and escalate to a human authority (desk supervisor / trade control); do not improvise.

## Adjacent-skill handoffs
See [references/handoffs.md](references/handoffs.md). Upstream monitoring/diagnosis skills may
hand a confirmed break here with a durable `break_id`; this skill owns the plan→execute
lifecycle and emits a `plan_id` + audit record. It never duplicates diagnosis-only,
settlement-monitoring, or regulatory-reporting work.

## Inputs and prerequisites
- A confirmed break: `break_id`, `trade_id`, type, evidence (firm booking + counterparty
  confirmation + supporting proof), and a proposed repair (action, amount, target, and
  `source` for a rebook). Schema: [scripts/validate_input.py](scripts/validate_input.py).
- The **permissible-repair catalog** and authority limits (versioned).
- Read access for planning; the approval-gated **execute** operation and an approver with the
  required role. See [references/controls.md](references/controls.md).

## Source hierarchy
See [references/source-map.md](references/source-map.md). The firm OMS/EMS is the system of
record being repaired; post-trade/clearing and the counterparty confirmation supply the
"true" economics to match against; market & reference data supplies instrument static and
calendars; the communications archive supplies agreed-terms evidence. The repair catalog and
limits are versioned contracts.

## Workflow (plan → validate → approve → execute → verify → audit)
1. **Match & classify** — reconcile the firm booking against the counterparty/clearing record;
   classify the break (mis-booked account, quantity, price, duplicate) and its economic
   difference; run `validate_input`.
2. **Select repair** — match to the permissible-repair catalog; confirm it is within the
   authority limit and its evidence requirements are met. If not → fail closed and escalate.
3. **Plan (deterministic)** — run
   [scripts/calculate_or_transform.py](scripts/calculate_or_transform.py) to build the repair
   plan: ordered steps each with an **idempotency key**, precondition, expected effect,
   **verification** check, and **rollback**; plus the expected post-state and the required
   approver role. The plan starts `approval: pending`, `execution: blocked`.
4. **Validate the plan** — run [scripts/validate_output.py](scripts/validate_output.py):
   amounts tie, repair is permissible and within the **catalog** authority limit for the break
   type (not the plan's self-declared limit), every step is idempotent + verifiable +
   reversible, plan_hash is present and matches (a missing/blank hash fails closed), and
   execution is blocked pending approval. Fail closed on any miss.
5. **Approve** — present the plan for human approval. Approval supplies an **approval token**
   bound to the plan hash and the approver's role. No token, no execution.
6. **Execute** — only with a valid token: run each step **idempotently** (re-running a step
   with the same idempotency key must not double-apply). Stop on the first failed
   precondition/verification.
7. **Verify** — confirm the actual post-state in the OMS/EMS equals the expected post-state;
   if not, invoke **rollback** and report.
8. **Audit** — record plan, approver, token, each step result, verification, and any rollback.

## Validation loop
`validate_input` before planning; `validate_output` after planning **and** before execution
(re-check the plan is still blocked/pending and unchanged). After execution, verify post-state;
on mismatch, roll back and fail closed. Never assume automatic retries.

## Human approval
`required` — **mandatory before any execution**. The approver must hold the **catalog-required**
approver role for the break type (recorded in the plan as `required_role`); the approval token
binds to the exact plan (hash) so an altered plan invalidates the approval. Authority limits are
enforced against the catalog for the break type; over-limit repairs require a higher approver and
are out of scope for auto-planning.

## Failure handling
- **Repair not permissible / over limit / missing evidence** → fail closed; escalate; no plan
  executes.
- **Precondition fails at execute** (e.g., counterparty/clearing already corrected the record)
  → stop; do not force; report the blocking state.
- **Verification mismatch after a step** → **roll back** that step and halt; report.
- **Partial completion / tool timeout** → leave the trade in a consistent state (rolled back
  to last verified checkpoint); never leave a half-applied repair; no silent retry.
- **Altered plan / stale token** → refuse to execute; re-plan and re-approve.

## Output contract
1. **Plan** — `plan_id`, break/trade, repair, amount, ordered steps (idempotency key,
   precondition, expected effect, verification, rollback), expected post-state, required
   approver role, `approval: pending`, `execution: blocked`.
2. **Validation result** — plan checks passed/failed.
3. **Execution record** (post-approval) — token, per-step result, verification, rollback if any.
4. **Audit trail** — actor, approver, timestamps, before/after state, citations.
5. **Standing note** — "Plan only; no system-of-record change has been executed. Execution
   requires human approval." (before execution).
See [references/controls.md](references/controls.md).

## Privacy and records
Customer NPI/PII and market-sensitive trade data. Mask account/trade identifiers to last 4 in
presentation. Retain plan, approval, execution, verification, and rollback records per
books-and-records requirements; the audit trail is immutable and complete. Log actor and
approver identities.

## Gotchas
- **Approval binds to the plan, not the break.** Editing the plan (amount, target, steps)
  after approval voids the token — re-approve.
- **Idempotency is mandatory.** A retried cancel/rebook/amend must be a no-op if already
  applied; use the idempotency key, never assume "it probably didn't book."
- **Reversibility first.** If a repair step cannot be rolled back, it needs a higher control
  and is out of scope for auto-planning.
- **Verify against the record, not the plan.** Post-state verification reads the OMS/EMS; do
  not "confirm" from the plan you just wrote.
- **Never widen the repair.** Fixing a mis-booked account does not authorize changing quantity,
  price, or settlement date unless the catalog repair explicitly includes them.
- **The counterparty/clearing side is the reference, not a writable target.** This skill
  repairs the firm's own booking; it never writes the counterparty, custodian, or CCP record.
