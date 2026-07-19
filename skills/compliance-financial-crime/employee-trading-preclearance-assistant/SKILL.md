---
name: employee-trading-preclearance-assistant
description: >-
  Pre-clear an employee personal-account trade: run the mandatory restricted-list, watch-list,
  blackout, minimum-holding, and conflicts/MNPI screens, derive the permissible decision
  (approve, conditional, or deny), and stage a validated, idempotent decision plan for
  authorized compliance approval and execution. Use when an employee-compliance or control-room
  analyst must check a proposed personal trade against restricted lists, holdings, blackout
  periods, conflicts, and policy rules and record a preclearance decision through a controlled
  plan → validate → approve → execute → verify → audit workflow. It records the decision and
  issues a time-boxed clearance only AFTER a valid compliance approval token bound to the plan
  hash. HARD BOUNDARY: it never auto-clears a hard-blocked trade (restricted list, blackout,
  minimum-holding breach, or conflict/MNPI force a deny), never records a decision or issues a
  clearance without approval, never lets an employee pre-clear their own trade, and never gives
  investment advice.
license: MIT
compatibility: Amazon Quick Desktop; requires employee-trading/preclearance-register, restricted/watch-list registers, wall-cross/MNPI + conflicts, employee-holdings feed, personal-trading policy corpus, and permission/approval-broker MCP integrations. Read-only for planning; the execute operation is approval-gated and idempotent.
metadata:
  aws-fsi-category: "Compliance & Financial Crime"
  aws-fsi-skill-type: "Workflow or orchestration skills"
  aws-fsi-risk-tier: "R4"
  aws-fsi-archetype: "Orchestrate & resolve"
  aws-fsi-agent-pattern: "Plan-validate-execute workflow agent"
  aws-fsi-delivery-wave: "Wave 4 - gated orchestration"
  aws-fsi-action-mode: "Approval-gated write or submission"
  aws-fsi-scheduled-agent: "no"
  aws-fsi-baseline-status: "new"
  aws-fsi-human-approval: "required"
  aws-fsi-data-classification: "Restricted (AML/BSA — SAR confidentiality; tipping-off controls)"
  aws-fsi-jurisdictions: "US (default); configure additional jurisdiction packs per deployment"
  aws-fsi-owner: "Compliance & Financial Crime (FIU)"
  aws-fsi-primary-user: "Employee-compliance / control-room analyst"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-07-17"
---

# Employee Trading Preclearance Assistant

## Purpose and outcome
Pre-clear an employee personal-account trade through a controlled workflow: run the mandatory
compliance screens, derive the **permissible** decision from the policy ruleset, build a
**validated decision plan** (idempotent steps, preconditions, expected post-state,
verification, rollback), and — **only after explicit compliance approval** — record the
decision and issue a time-boxed clearance, leaving a complete audit trail. The outcome is a
preclearance decision (`approve`, `approve_with_conditions`, or `deny`) with evidence that
every screen was run, the decision was authorized, and any clearance is verified and
reversible.

## Use when
- "Pre-clear my personal trade — check it against the restricted list, blackout, holdings,
  and conflicts, then route it for compliance approval."
- "Build the preclearance decision plan for request X and route it to a compliance officer."
- "The officer approved this decision — record it and issue the clearance window."

## Do not use
- **Holdings summary / analysis only** with no preclearance intent → use
  `portfolio-holdings-summarizer`; this skill is for a staged, gated decision.
- **Firm/fund portfolio orders** tested against mandate/guideline rules → `mandate-compliance-monitor`.
- **Suspected market abuse** (trading on MNPI, front-running) → `surveillance-alert-triager` /
  `market-surveillance-alert-investigator`.
- **Conflict adjudication** as the core question → `conflicts-of-interest-reviewer`.
- **Personalized investment advice** ("is this a good trade?") → prohibited; do not opine.
- Any request over the senior authority limit, or a policy override/hardship → stop and
  escalate to the Chief Compliance Officer; do not improvise.

## Adjacent-skill handoffs
See [references/handoffs.md](references/handoffs.md). Upstream intake hands a personal-trade
request here with a durable `request_id`; a confirmed conflict may arrive from
`conflicts-of-interest-reviewer` as the `conflicts_mnpi` screen result. This skill owns the
plan → execute lifecycle and emits a `plan_id` + audit record. It never investigates market
abuse, adjudicates conflicts, or acts on firm/fund orders.

## Inputs and prerequisites
- A preclearance request: `request_id`, employee/account, `instrument` (symbol, issuer, asset
  class), `side`, `quantity`, `notional_usd`, `request_date`, and the results of **all
  mandatory screens** (restricted list, watch list, blackout, minimum-holding, conflicts/MNPI).
  Schema: [scripts/validate_input.py](scripts/validate_input.py).
- The **personal-trading policy** (versioned): restricted/watch lists, blackout calendars,
  thresholds, minimum-holding period, and the decision-authority matrix.
- Read access for planning; the approval-gated **execute** operation and an approver who holds
  the required role and is **not** the requesting employee. See
  [references/controls.md](references/controls.md).

## Source hierarchy
See [references/source-map.md](references/source-map.md). The employee-trading / preclearance
register is the system of record; restricted/watch-list registers, wall-cross/MNPI + conflicts
lists, the holdings feed, and the policy corpus are versioned read-only contracts; the
approval broker issues tokens and gates execution.

## Workflow (plan → validate → approve → execute → verify → audit)
1. **Intake & screen** — confirm the request and that every mandatory screen was performed;
   run [scripts/validate_input.py](scripts/validate_input.py). Fail closed on a missing screen.
2. **Derive decision (deterministic)** — run
   [scripts/calculate_or_transform.py](scripts/calculate_or_transform.py). Any hard block
   (restricted-list hit, active blackout, minimum-holding breach, conflict/MNPI flag) forces a
   `deny`; a watch-list hit or notional over the analyst limit yields
   `approve_with_conditions`; otherwise `approve`. Notional over the senior limit yields a
   **rejected** plan that escalates to the CCO. See [references/domain-rules.md](references/domain-rules.md).
3. **Plan** — the builder produces ordered steps (record decision, issue clearance window,
   apply conditions, append audit), each with an **idempotency key**, precondition, expected
   effect, **verification**, and **rollback**; plus the expected post-state, the required
   approver role, and the **plan hash**. The plan starts `approval: pending`, `execution: blocked`.
4. **Validate the plan** — run [scripts/validate_output.py](scripts/validate_output.py): the
   decision is permissible (no approve* over a hard block), notional is in limit, every step is
   idempotent + verifiable + reversible, the clearance ties to the notional, and execution is
   blocked pending approval. Fail closed on any miss.
5. **Approve** — present the plan for compliance approval. Approval supplies a **token** bound
   to the plan hash and the approver's role. No token, no execution; approver ≠ employee.
6. **Execute** — only with a valid token: run each step **idempotently** (re-running a step
   with the same key must not double-record or double-clear). Stop on the first failed
   precondition/verification.
7. **Verify** — confirm the register's post-state equals the expected post-state (decision
   recorded, clearance active, conditions applied); if not, invoke **rollback** and report.
8. **Audit** — record plan, screens (with versions), approver, token, per-step result,
   verification, and any rollback.

## Validation loop
`validate_input` before planning; `validate_output` after planning **and** before execution
(re-check the plan is still blocked/pending and unchanged). After execution, verify the
register post-state; on mismatch, roll back and fail closed. Never assume automatic retries.

## Human approval
`required` — **mandatory before any decision is recorded or any clearance is issued.** The
approver must hold the role named in the plan (`compliance-preclearance-analyst` for standard
approvals, `compliance-officer` for conditional/deny), must **not** be the requesting employee
(segregation of duties), and the token binds to the exact plan (hash) so an altered plan voids
the approval. Notional over the senior limit requires the CCO and is out of scope for
auto-planning.

## Failure handling
- **Mandatory screen not performed / missing result** → fail closed; no plan is built.
- **Hard block present** → decision is `deny`; the builder never emits an `approve*` plan, and
  `validate_output` rejects one that claims to.
- **Notional over the senior limit** → rejected plan; escalate to the CCO; nothing executes.
- **Precondition fails at execute** (e.g., a prior decision already exists) → stop; do not
  force; report the blocking state.
- **Verification mismatch after a step** → **roll back** that step and halt; report.
- **Partial completion / tool timeout** → leave the request at the last verified checkpoint
  (decision voided / clearance revoked); never leave a half-recorded decision; no silent retry.
- **Altered plan / stale token / approver = employee** → refuse to execute; re-plan / re-approve.

## Output contract
1. **Plan** — `plan_id`, request/employee, instrument, side, quantity, notional, `decision`,
   `hard_blocks`, conditions, ordered steps (idempotency key, precondition, expected effect,
   verification, rollback, post-state), expected post-state, authority limit, required approver
   role, `approval: pending`, `execution: blocked`, plan hash.
2. **Validation result** — plan checks passed/failed.
3. **Execution record** (post-approval) — token, per-step result, verification, rollback if any.
4. **Audit trail** — actor, approver, timestamps, screens relied on (versions), before/after state.
5. **Standing note** — "Decision plan only; no preclearance decision has been recorded and no
   clearance has been issued. Execution requires compliance approval." (before execution).
See [references/controls.md](references/controls.md).

## Privacy and records
Restricted (AML/BSA — SAR confidentiality; tipping-off controls). Employee personal-trading
data and MNPI are highly sensitive. Mask employee/account identifiers to last 4 in
presentation; restrict MNPI details to entitled reviewers. Retain plan, approval, execution,
verification, and rollback records per the personal-trading recordkeeping schedule; the audit
trail is immutable and complete. Log actor and approver identities.

## Gotchas
- **Hard blocks are not negotiable.** A restricted-list hit, active blackout, minimum-holding
  breach, or MNPI/conflict flag can only produce a `deny` — never talk yourself into an approve.
- **Approval binds to the plan, not the request.** Editing the decision, notional, or steps
  after approval voids the token — re-approve.
- **The employee cannot clear their own trade.** Segregation of duties is enforced at execute;
  an approver equal to the requesting employee fails closed.
- **Clearance is time-boxed and scoped.** It authorizes the requested instrument, side, and up
  to the requested notional for the window only; it is not a standing authorization.
- **A buy locks the holding period.** Every approved buy records a `min_holding_lock`; a later
  sell inside that window is caught by the minimum-holding screen — do not override it.
- **Verify against the register, not the plan.** Post-state verification reads the preclearance
  register; do not "confirm" from the plan you just wrote.
