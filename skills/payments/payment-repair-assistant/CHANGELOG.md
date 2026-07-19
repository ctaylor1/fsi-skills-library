# Changelog — payment-repair-assistant

## [0.1.0] — 2026-07-17
Initial authoring in the FSI Skills Library (baseline status: `new`). The Payments R4
gated-orchestration skill; mirrors the `loan-servicing-exception-resolver` exemplar.

- **Scope:** plan → validate → approve → execute → verify → audit for rejected or held
  payments (invalid beneficiary detail, missing remittance info, missing purpose code,
  screening-cleared hold, unrecoverable reject).
- **Controls:** R4; execution (resubmit / release / return) is approval-gated and
  idempotent; permissible-repair catalog with authority limits; **sanctions-screening gate**
  (no resubmission/release on an uncleared hit or pending disposition); approval token binds
  to the plan hash + approver role; idempotency key bound to the payment end-to-end id
  (duplicate-payment guard); verification reads the system of record and confirms a single
  submission; rollback via camt.056 recall/return, re-hold, or field restore; immutable audit
  trail; segregation of duties (planner ≠ approver; screening owned by compliance); no silent
  retries.
- **Scripts:** `validate_input` (catalog/limit/evidence/reversibility/screening/end-to-end
  checks), plan builder (idempotent steps, preconditions, verification, rollback, expected
  post-state, plan hash, blocked/pending posture), `validate_output` (catalog/limit,
  screening gate, step completeness, end-to-end binding, tamper detection via plan_hash,
  pre-execution blocked/pending, executed-without-approval block, amount tie-out, standing
  note).
- **Evaluations:** trigger/routing, golden beneficiary-repair plan, deterministic script
  checks, executed-without-approval + over-limit + tampered-plan + uncleared-screening +
  duplicate-guard safety, approval-authorization, idempotency.
- **Handoffs:** upstream from `payment-exception-investigator` /
  `payment-failure-diagnoser` / `iso-20022-message-interpreter`; lateral to
  `payment-fraud-case-investigator`, `settlement-break-reconciler`,
  `transaction-reconciliation-helper`, `dispute-operations-assistant`; uncleared screening →
  sanctions/compliance; out-of-catalog/over-limit → higher approver / policy-exception
  process.

### Pending before release
- Payments controls owner + operational-risk and sanctions/compliance blind review; SoD and
  rollback (recall/return) tabletop test.
- Confirm the permissible-repair catalog, authority limits, and approver-role registry
  (versioned), and the approval-broker and screening-disposition contracts.
- Wire the approval-gated, idempotent `payops.apply_repair / resubmit / release / return /
  verify / rollback` MCP operations and the append-only audit sink at deployment.
