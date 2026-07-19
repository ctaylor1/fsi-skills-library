---
name: corporate-action-election-assistant
description: >-
  Validate a voluntary corporate-action election end to end — eligible record-date position,
  submission deadline, permissible options, and instructed quantity — then build a validated,
  idempotent election plan and, only AFTER an authorized human approval bound to the plan,
  submit it to the custodian/agent, verify the acknowledgment, and leave an audit trail with
  rollback. Use when a corporate-actions operations specialist needs to stage and submit a
  tender, exchange, optional/scrip dividend, rights subscription, or conversion election
  through a controlled plan → validate → approve → submit → verify → audit workflow. HARD
  BOUNDARY: it never submits, records, withdraws, or confirms an election without a valid
  approval token bound to the plan hash and approver role; never over-elects the eligible
  position, elects past the deadline, or elects an off-catalog/over-limit option; and never
  recommends which option to choose or gives investment or tax advice.
license: MIT
compatibility: Amazon Quick Desktop; requires post-trade/clearing (depository/agent election gateway), portfolio-accounting/custody, market/reference-data, document-intelligence, and permission/approval-broker MCP integrations. Read-only for planning; the submit operation is approval-gated and idempotent.
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
  aws-fsi-primary-user: "Corporate-actions operations specialist"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-07-17"
---

# Corporate Action Election Assistant

## Purpose and outcome
Process a **voluntary** corporate-action election through a controlled workflow: confirm the
eligible record-date position, the option the holder has chosen, the instructed quantity, and
the submission deadline; build a **validated election plan** (idempotent legs, preconditions,
expected post-state, verification, rollback); and — **only after explicit human approval** —
submit it to the custodian/agent, verify the acknowledgment, and leave a complete audit trail.
The outcome is a submitted, acknowledged election with evidence that it was eligible,
in-window, within the authority limit, authorized, verified, and reversible before the
deadline.

## Use when
- "Validate my eligible position for this optional dividend and stage the election for
  approval."
- "Prepare the tender / exchange / rights-subscription / conversion election for N of my
  eligible shares and route it for authorized submission."
- "The election is approved — submit the instruction to the agent and verify it was
  acknowledged."

## Do not use
- **Interpretation / explanation** of the event, options, dates, or entitlements with no
  election intent → use `corporate-action-interpreter`.
- **Which option is better / whether to participate** (investment advice) → out of scope; a
  licensed representative must handle it. This skill never recommends an option.
- **Personalized tax result or cost-basis treatment** → out of scope; refer to a licensed tax
  professional.
- **Settlement of the elected proceeds/positions** → `post-trade-settlement-monitor`.
- **A trade/position break across systems** (not a CA election) → `trade-break-resolver`.
- Any option **not in the permissible catalog**, an instructed quantity **over the eligible
  position**, a notional **over the authority limit**, an **irreversible** event, or a request
  **past the submission cutoff** → stop and escalate to a human authority; do not improvise.

## Adjacent-skill handoffs
See [references/handoffs.md](references/handoffs.md). Upstream `corporate-action-interpreter`
(with an `interpretation_id`) and `portfolio-holdings-summarizer` (eligible position) may seed
this skill; it owns the plan→submit lifecycle and emits a `plan_id` + audit record. It never
duplicates interpretation, settlement, or break-resolution work, and never advises on option
choice.

## Inputs and prerequisites
- A confirmed election request: `event_id`, `account`, `event_type`, `eligible_quantity`,
  `reference_price`, `as_of`, `submission_deadline`, `evidence{...}`, and a
  `proposed_election` (legs `[{option, quantity}]` or a single `option`+`quantity`). Optional
  `interpretation_id`, `market_deadline`, `catalog_version`. Schema:
  [scripts/validate_input.py](scripts/validate_input.py).
- The **permissible-election catalog**, per-event caps, and notional authority limits
  (versioned).
- Read access for planning; the approval-gated **submit** operation and an approver holding
  the required role. See [references/controls.md](references/controls.md).

## Source hierarchy
See [references/source-map.md](references/source-map.md). The depository/agent **official
notice** is authoritative for terms and deadlines; custody supplies the eligible record-date
position; reference data supplies the price for notional. The catalog, caps, and limits are
versioned contracts. Never let an interpretation or a user assertion override the official
notice.

## Workflow (plan → validate → approve → submit → verify → audit)
1. **Confirm the request** — one event, one account; confirm the chosen option(s), quantity,
   eligible record-date position, and both deadlines; run `validate_input`.
2. **Screen against the catalog** — option permissible for the event type; instructed
   quantity within the eligible position (or oversubscription cap); notional within the
   authority limit; event reversible; `as_of` before the submission cutoff. If not → fail
   closed and escalate.
3. **Plan (deterministic)** — run
   [scripts/calculate_or_transform.py](scripts/calculate_or_transform.py) to build the
   election plan: ordered legs each with an **idempotency key**, precondition, expected effect,
   **verification** check, and **rollback**; plus the expected post-state and a **plan hash**.
   The plan starts `approval: pending`, `execution: blocked`.
4. **Validate the plan** — run [scripts/validate_output.py](scripts/validate_output.py):
   options permissible, quantities tie and do not over-elect, notional in limit and ties,
   in-window, every leg idempotent + verifiable + reversible, hash intact, and submission
   blocked pending approval. Fail closed on any miss.
5. **Approve** — present the plan for human approval. Approval supplies an **approval token**
   bound to the plan hash and the approver's role. No token, no submission.
6. **Submit** — only with a valid token: submit each leg **idempotently** (re-submitting a leg
   with the same idempotency key must not double-elect). Stop on the first failed
   precondition/verification.
7. **Verify** — confirm the custodian/agent acknowledgment matches the intended option and
   quantity; if not, **withdraw/supersede** before the deadline and report.
8. **Audit** — record plan, approver, token, each leg result, acknowledgment, and any rollback.

## Validation loop
`validate_input` before planning; `validate_output` after planning **and** before submission
(re-check the plan is still blocked/pending, in-window, and unchanged). After submission,
verify the acknowledgment; on mismatch, withdraw/supersede and fail closed. Never assume
automatic retries.

## Human approval
`required` — **mandatory before any submission**. The approver must hold the role named in the
plan; the approval token binds to the exact plan (hash) so an altered plan invalidates the
approval. Notional authority limits are enforced; over-limit elections require a higher
approver and are out of scope for auto-planning.

## Failure handling
- **Option off-catalog / over eligible / over limit / irreversible / past cutoff** → fail
  closed; escalate; no plan is submitted.
- **Precondition fails at submit** (position changed, window closed) → stop; do not force;
  report the blocking state.
- **Acknowledgment mismatch after a leg** → **withdraw/supersede** that leg before the
  deadline and halt; report.
- **Partial completion / tool timeout** → leave the account in a consistent state (submitted
  legs withdrawn to the last verified checkpoint before the deadline); never leave a
  half-submitted election; no silent retry.
- **Altered plan / stale token / closed window** → refuse to submit; re-plan and re-approve
  (or escalate a late/protect instruction to operations).

## Output contract
1. **Plan** — `plan_id`, event/account, event type, option legs (idempotency key, precondition,
   expected effect, verification, rollback), instructed/eligible quantity, notional, authority
   limit, expected post-state, required approver role, `approval: pending`, `execution:
   blocked`.
2. **Validation result** — plan checks passed/failed.
3. **Submission record** (post-approval) — token, per-leg result, acknowledgment, rollback if
   any.
4. **Audit trail** — actor, approver, timestamps, before/after state, citations.
5. **Standing note** — "Plan only; no election has been submitted to the custodian or agent.
   Submission requires human approval." (before submission).
See [references/controls.md](references/controls.md).

## Privacy and records
Customer NPI/PII. Mask account identifiers to last 4 in presentation. Retain plan, approval,
submission, acknowledgment, and rollback records per corporate-actions recordkeeping; the
audit trail is immutable and complete. Log actor and approver identities.

## Gotchas
- **Approval binds to the plan, not the event.** Editing the quantity or option after approval
  voids the token — re-approve.
- **Eligibility is the record-date holding**, not today's position. A differing `as_of` is
  surfaced, not silently used; never over-elect.
- **Two deadlines.** Plan and submit before the **agent/custodian cutoff**; the later
  market/protect deadline is not the submission window. Past the cutoff → fail closed.
- **Idempotency is mandatory.** A retried leg must be a no-op if already acknowledged; use the
  idempotency key, never assume "it probably didn't go through."
- **Reversibility first.** If an election cannot be amended/withdrawn before the deadline it is
  out of scope for auto-planning.
- **Verify against the acknowledgment, not the plan.** Post-submission verification reads the
  custodian/agent; do not "confirm" from the plan you just wrote.
- **Never advise the choice.** Validating and submitting the holder's chosen option is in
  scope; saying which option to pick, or that it is "tax-free", is advice and out of scope.
