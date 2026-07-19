---
name: payment-repair-assistant
description: >-
  Construct a validated repair plan for a rejected or held payment from an approved
  payment-exception or investigation case: confirm case and payment identity, apply a
  permissible repair (correct beneficiary/remittance/purpose data, release a
  screening-cleared hold, or return an unrecoverable reject), verify beneficiary and
  sanctions-screening data, and stage an idempotent plan → validate → approve → execute →
  verify → audit workflow with rollback. Use when a payments investigations/repair
  specialist must resolve a rejected or held ISO 20022 payment end to end with a controlled,
  gated resubmission. HARD BOUNDARY: it never resubmits, releases, returns, or cancels a
  payment without a valid human approval token bound to the exact plan hash; it never
  resubmits a payment whose sanctions screening is not cleared, never exceeds the repair
  authority limit, and never applies a repair outside the permissible catalog — it fails
  closed and escalates instead.
license: MIT
compatibility: Amazon Quick Desktop; requires payment-operations/rail-connectivity, ISO 20022 message, sanctions/screening, entity-resolution (beneficiary), document-intelligence, and permission/approval-broker MCP integrations. Read-only for planning; the resubmit/release/return operation is approval-gated, idempotent, and reversible.
metadata:
  aws-fsi-category: "Payments"
  aws-fsi-skill-type: "Workflow or orchestration skills"
  aws-fsi-risk-tier: "R4"
  aws-fsi-archetype: "Orchestrate & resolve"
  aws-fsi-agent-pattern: "Plan-validate-execute workflow agent"
  aws-fsi-delivery-wave: "Wave 4 - gated orchestration"
  aws-fsi-action-mode: "Approval-gated write or submission"
  aws-fsi-scheduled-agent: "no"
  aws-fsi-baseline-status: "new"
  aws-fsi-human-approval: "required"
  aws-fsi-data-classification: "Highly Confidential (customer NPI/PII; cardholder data)"
  aws-fsi-jurisdictions: "US (default); configure additional jurisdiction packs per deployment"
  aws-fsi-owner: "Payments operations & risk"
  aws-fsi-primary-user: "Payments investigations / repair team"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-07-17"
---

# Payment Repair Assistant

## Purpose and outcome
Resolve a rejected or held payment through a controlled workflow: confirm the case and
payment identity, select a **permissible** repair from the approved catalog, build a
**validated repair plan** (idempotent steps, preconditions, expected post-state,
verification, rollback), and — **only after explicit human approval** — resubmit, release,
or return the payment and verify the result, leaving a complete audit trail. The outcome is
a corrected, single, successfully resubmitted (or returned) payment with evidence that the
beneficiary and sanctions data were confirmed and that every action was authorized,
verified, and reversible.

## Use when
- "Build the repair plan for this approved payment-exception case and route it for approval."
- "Screening cleared this held wire as a false positive — plan the release and resubmission."
- "Return this unrecoverable reject to the originator."
- "Execute the approved repair plan and verify the payment resubmitted exactly once."

## Do not use
- **Diagnosis only** — tracing why a payment failed or parsing a message with no repair
  intent → use `payment-failure-diagnoser` or `iso-20022-message-interpreter`.
- **Building the exception chronology / investigation** → `payment-exception-investigator`
  (upstream; it hands a confirmed, screening-dispositioned case here).
- **Suspected fraud / account takeover** on the payment → `payment-fraud-case-investigator`.
- **Settlement-file or ledger breaks** → `settlement-break-reconciler` /
  `transaction-reconciliation-helper`.
- **Card dispute / chargeback representment** → `dispute-operations-assistant`.
- Any repair **not in the permissible catalog**, over the authority limit, irreversible, or
  whose **sanctions screening is not cleared** → stop and escalate to a human authority
  (sanctions/compliance or a higher approver); do not improvise.

## Adjacent-skill handoffs
See [references/handoffs.md](references/handoffs.md). `payment-exception-investigator` hands
a confirmed exception here with a durable `case_id` and screening disposition; this skill
owns the plan → execute lifecycle and emits a `plan_id` + audit record. It never duplicates
diagnosis, investigation, fraud, reconciliation, or dispute work, and only this skill
executes the repair.

## Inputs and prerequisites
- An approved case: `case_id`, `payment_id`, exception `type`, `end_to_end_id`, `rail`,
  `screening` disposition, `evidence`, beneficiary/customer data, and a proposed repair
  (action, amount, currency, field/new value, target). Schema:
  [scripts/validate_input.py](scripts/validate_input.py).
- The **permissible-repair catalog** and repair authority limits (versioned).
- A cleared **sanctions screening** disposition for any resubmission/release.
- Read access for planning; the approval-gated **execute** operation and an approver with
  the required role. See [references/controls.md](references/controls.md).

## Source hierarchy
See [references/source-map.md](references/source-map.md). The payment-operations system is
the system of record for payment status and preconditions; the ISO 20022 message store and
document-intelligence supply the original message and repair evidence; entity resolution
confirms the beneficiary; the sanctions/screening service supplies the cleared disposition.
The repair catalog and limits are versioned contracts.

## Workflow (plan → validate → approve → execute → verify → audit)
1. **Confirm identity** — verify the `case_id`/`payment_id`/`end_to_end_id` match the held
   or rejected payment; run `validate_input`.
2. **Select repair** — match the exception to the permissible-repair catalog; confirm it is
   within the authority limit, its evidence is complete, and — for a resubmission/release —
   the **screening is cleared**. If not → fail closed and escalate.
3. **Plan (deterministic)** — run
   [scripts/calculate_or_transform.py](scripts/calculate_or_transform.py) to build the
   repair plan: ordered steps each with an **idempotency key** (bound to the end-to-end id),
   precondition, expected effect, **verification** (single submission, no duplicate), and
   **rollback** (recall/return via camt.056, re-hold, or restore field); plus the expected
   post-state and required approver role. The plan starts `approval: pending`,
   `execution: blocked`.
4. **Validate the plan** — run [scripts/validate_output.py](scripts/validate_output.py):
   repair permissible/in-limit, screening cleared, every step idempotent + verifiable +
   reversible + bound to the end-to-end id, plan hash present and intact (a missing/blank
   hash fails closed), and execution blocked pending approval. Fail closed on any miss.
5. **Approve** — present the plan for human approval. Approval supplies an **approval token**
   bound to the plan hash and the approver's role. No token, no execution.
6. **Execute** — only with a valid token: run each step **idempotently** (re-running a step
   with the same end-to-end key must not resubmit the payment twice). Stop on the first
   failed precondition/verification.
7. **Verify** — confirm the payment reached the expected post-state and exactly one
   submission/return occurred; if not, invoke **rollback** and report.
8. **Audit** — record plan, approver, token, each step result, verification, and any
   rollback.

## Validation loop
`validate_input` before planning; `validate_output` after planning **and** before execution
(re-check the plan is still blocked/pending, screening still cleared, and the hash
unchanged). After execution, verify the actual payment status; on mismatch or a suspected
duplicate, roll back and fail closed. Never assume automatic retries — a blind retry is how
payments get sent twice.

## Human approval
`required` — **mandatory before any execution**. The approver must hold the role named in
the plan; the approval token binds to the exact plan (hash) so an altered plan (amount,
beneficiary, target) invalidates the approval. Repair authority limits are enforced;
over-limit repairs require a higher approver and are out of scope for auto-planning.

## Failure handling
- **Repair not permissible / over limit / missing evidence** → fail closed; escalate; no plan
  executes.
- **Screening not cleared (hit or pending)** → fail closed; route to sanctions/compliance;
  never resubmit or release.
- **Precondition fails at execute** (already resubmitted, already returned, no longer held) →
  stop; do not force; report the blocking state.
- **Verification mismatch / suspected duplicate** → **roll back** (recall/return) and halt;
  report.
- **Partial completion / tool timeout** → leave the payment in a consistent state (rolled
  back to last verified checkpoint); never leave a half-applied repair or an ambiguous
  double submission; no silent retry.
- **Altered plan / stale token** → refuse to execute; re-plan and re-approve.

## Output contract
1. **Plan** — `plan_id`, case/payment, repair, amount/currency, ordered steps (idempotency
   key, precondition, expected effect, verification, rollback, end-to-end binding on movement
   steps), expected post-state and status, required approver role, `approval: pending`,
   `execution: blocked`.
2. **Validation result** — plan checks passed/failed.
3. **Execution record** (post-approval) — token, per-step result, verification, rollback if any.
4. **Audit trail** — actor, approver, timestamps, before/after status, screening disposition,
   citations.
5. **Standing note** — "Plan only; no payment has been resubmitted, released, returned, or
   cancelled. Execution requires human approval." (before execution).
See [references/controls.md](references/controls.md).

## Privacy and records
Customer NPI/PII and cardholder data. Mask payment/account/beneficiary identifiers to last 4
in presentation. Retain plan, screening disposition, approval, execution, verification, and
rollback records per payments recordkeeping; the audit trail is immutable and complete. Log
actor and approver identities.

## Gotchas
- **Idempotency prevents double payments.** A retried movement step must be a no-op if the
  end-to-end id already resubmitted; never assume "it probably didn't go through."
- **Screening is a gate, not a warning.** An uncleared hit or a pending disposition blocks
  the plan — this skill does not adjudicate screening; sanctions/compliance does.
- **Approval binds to the plan, not the case.** Editing the amount or beneficiary after
  approval voids the token — re-approve.
- **Verify against the rail, not the plan.** Post-state verification reads the
  payment-operations system for the actual status; do not "confirm" from the plan you wrote.
- **Never widen the repair.** Fixing a beneficiary BIC does not authorize changing the
  amount, debtor, or value date unless the catalog repair explicitly includes them.
- **Reversibility first.** If a repair step cannot be recalled/returned/re-held, it needs a
  higher control and is out of scope for auto-planning.
