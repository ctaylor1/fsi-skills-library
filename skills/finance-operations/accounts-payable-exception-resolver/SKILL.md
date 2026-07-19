---
name: accounts-payable-exception-resolver
description: >-
  Investigate an accounts-payable exception (invoice price variance, PO quantity variance,
  goods-receipt mismatch, duplicate invoice, tax miscode, supplier bank-detail mismatch,
  or missing approval), identify the root cause and the permissible remedy, and stage a
  validated correction plan for authorized approval and execution against the AP subledger.
  Use when an accounts-payable or procurement-operations specialist needs to resolve an
  invoice/PO/receipt exception end to end with a controlled plan → validate → approve →
  execute → verify → audit workflow. This skill produces and, only AFTER an explicit human
  approval token bound to the plan, executes an idempotent correction with verification and
  rollback. HARD BOUNDARY: it never disburses funds, releases a payment run, initiates a
  bank transfer, or changes supplier banking details; it only corrects AP-record matching,
  tax coding, and payment-hold / approval-routing state, and only after that approval.
license: MIT
compatibility: Amazon Quick Desktop; requires ERP/AP-subledger, procurement/PO, goods-receipt, document-intelligence, approved-calculation, and permission/approval-broker MCP integrations. Read-only for planning; the execute operation is approval-gated and idempotent. No disbursement or payment-run integration is bound.
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
  aws-fsi-primary-user: "Accounts-payable / procurement operations"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-07-17"
---

# Accounts-Payable Exception Resolver

## Purpose and outcome
Resolve an accounts-payable exception through a controlled workflow: diagnose the root
cause, select a **permissible** remedy from the approved catalog, build a **validated
correction plan** (idempotent steps, preconditions, expected post-state, verification,
rollback), and — **only after an explicit human approval token bound to the plan** —
execute the correction against the AP subledger and verify the result, leaving a complete
audit trail. The outcome is a corrected AP record (three-way match, tax coding, or
payment-hold / approval-routing state) with evidence that every change was authorized,
verified, and reversible. Disbursement stays outside this skill.

## Use when
- "Resolve this invoice price variance / this PO quantity variance / this goods-receipt
  mismatch and route the correction for approval."
- "This invoice is a duplicate — stage a payment hold and route it."
- "The tax code on this invoice is wrong — build the correction plan."
- "The supplier bank details on this invoice don't match the master — hold it pending
  verification."
- "This invoice is missing the required approval — route it per the delegation of authority."
- "Execute the approved AP correction and verify it posted."

## Do not use
- **Diagnosis / analysis only** with no correction intent → use an invoice-review or
  `gl-reconciler` analysis; this skill is for staged, gated resolution.
- **General-ledger reconciliation breaks** (not an AP invoice/PO/receipt exception) →
  `gl-reconciler`.
- **Period-close orchestration** across the ledger → `month-end-close-orchestrator`.
- **Loan-servicing exceptions** → `loan-servicing-exception-resolver`.
- **Supplier onboarding / bank-master change approval** → a vendor-master control and the
  `third-party-risk-assessor` / procurement process; this skill only *holds* an invoice on a
  bank-detail mismatch, it never changes banking details.
- **Disbursing funds, releasing a payment run, or initiating a transfer** → out of scope for
  every remedy; that is a separate treasury / payment-run control. Do not improvise.
- Any remedy **not in the permissible catalog**, over the monetary authority limit, or
  requiring a policy exception → stop and escalate to a human authority.

## Adjacent-skill handoffs
See [references/handoffs.md](references/handoffs.md). Upstream review skills may hand a
confirmed exception here with a durable `exception_id`; this skill owns the plan→execute
lifecycle and emits a `plan_id` + audit record. It never duplicates diagnosis-only work,
GL reconciliation (`gl-reconciler`), or period-close orchestration
(`month-end-close-orchestrator`).

## Inputs and prerequisites
- A confirmed exception: `exception_id`, `invoice_id`, `vendor_id`, type, evidence, and a
  proposed remedy (action, amount, target). Schema:
  [scripts/validate_input.py](scripts/validate_input.py).
- The **permissible-remedy catalog** and monetary authority limits (versioned).
- Read access for planning; the approval-gated **execute** operation and an approver with
  the required role. See [references/controls.md](references/controls.md).

## Source hierarchy
See [references/source-map.md](references/source-map.md). The ERP AP subledger is the system
of record; procurement (PO) and goods-receipt systems supply match evidence;
document-intelligence extracts the invoice; the calculation service computes remedy amounts
and expected post-state. The remedy catalog and limits are versioned contracts.

## Workflow (plan → validate → approve → execute → verify → audit)
1. **Diagnose** — confirm the exception, root cause, and evidence (invoice vs PO vs
   receipt, duplicate proof, tax determination, or bank-master delta); run `validate_input`.
2. **Select remedy** — match to the permissible-remedy catalog
   ([references/domain-rules.md](references/domain-rules.md)); confirm it is within the
   monetary authority limit and its evidence requirements are met. If not → fail closed and
   escalate.
3. **Plan (deterministic)** — run
   [scripts/calculate_or_transform.py](scripts/calculate_or_transform.py) to build the
   correction plan: ordered steps each with an **idempotency key**, precondition, expected
   effect, **verification** check, and **rollback**; plus the expected post-state, plan
   hash, and the required approver role. The plan starts `approval: pending`,
   `execution: blocked`.
4. **Validate the plan** — run [scripts/validate_output.py](scripts/validate_output.py):
   remedy is permissible/in-limit, amounts tie, every step is idempotent + verifiable +
   reversible and its action is on the permissible-operation allowlist, the plan hash is
   present and matches, and execution is blocked pending approval. Fail closed on any miss
   (a missing plan hash or a non-allowlisted step action is a failure, never a skip).
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
post-state against the AP subledger; on mismatch, roll back and fail closed. Never assume
automatic retries.

## Human approval
`required` — **mandatory before any execution**. The approver must hold the role named in
the plan; the approval token binds to the exact plan (hash) so an altered plan invalidates
the approval. Monetary authority limits are enforced; over-limit remedies require a higher
approver and are out of scope for auto-planning. No remedy releases payment.

## Failure handling
- **Remedy not permissible / over limit / missing evidence** → fail closed; escalate; no plan
  executes.
- **Precondition fails at execute** (e.g., invoice already paid, hold already lifted, PO
  closed) → stop; do not force; report the blocking state.
- **Verification mismatch after a step** → **roll back** that step and halt; report.
- **Partial completion / tool timeout** → leave the AP record in a consistent state (rolled
  back to last verified checkpoint); never leave a half-applied correction; no silent retry.
- **Altered plan / stale token** → refuse to execute; re-plan and re-approve.
- **Bank-detail mismatch** → the only permissible remedy is a protective **hold**; never
  update the supplier bank master and never release payment.

## Output contract
1. **Plan** — `plan_id`, exception/invoice/vendor, remedy, amount, ordered steps
   (idempotency key, precondition, expected effect, verification, rollback), expected
   post-state, plan hash, required approver role, `approval: pending`, `execution: blocked`.
2. **Validation result** — plan checks passed/failed.
3. **Execution record** (post-approval) — token, per-step result, verification, rollback if
   any.
4. **Audit trail** — actor, approver, timestamps, before/after state, citations.
5. **Standing note** — "Plan only; no system-of-record change has been executed. Execution
   requires human approval." (before execution).
See [references/controls.md](references/controls.md).

## Privacy and records
Confidential financial records; supplier data may include PII. Mask vendor/bank identifiers
to last 4 in presentation. Retain plan, approval, execution, verification, and rollback
records per AP/records-retention policy; the audit trail is immutable and complete. Log
actor and approver identities.

## Gotchas
- **Approval binds to the plan, not the exception.** Editing the plan after approval voids
  the token — re-approve.
- **Never disburse.** No remedy pays, releases a payment run, or moves funds; a bank-detail
  mismatch results in a hold, never a bank-master change.
- **Idempotency is mandatory.** A retried step must be a no-op if already applied; use the
  idempotency key, never assume "it probably didn't post."
- **Verify against the subledger, not the plan.** Post-state verification reads the AP
  system of record; do not "confirm" from the plan you just wrote.
- **Never widen the remedy.** Fixing a price variance does not authorize touching quantity,
  tax, or other invoice lines unless the catalog remedy explicitly includes them.
- **Duplicate ≠ delete.** A duplicate invoice is *blocked/held*, not hard-deleted; the
  original stays payable.
