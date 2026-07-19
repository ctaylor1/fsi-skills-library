# Changelog — accounts-payable-exception-resolver

## [0.1.0] — 2026-07-18
Initial authoring in the FSI Skills Library (baseline status: `new`). Finance & Operations
R4 gated-orchestration skill, mirroring the banking `loan-servicing-exception-resolver`
exemplar.

- **Scope:** plan → validate → approve → execute → verify → audit for AP exceptions
  (invoice price variance, PO quantity variance, goods-receipt mismatch, duplicate invoice,
  tax miscode, supplier bank-detail mismatch, missing approval).
- **Hard boundary:** never disburses funds, releases a payment run, initiates a transfer, or
  changes supplier banking details; corrections touch AP-record matching, tax coding, and
  payment-hold / approval-routing state only, and only after approval.
- **Controls:** R4; execution is approval-gated and idempotent; permissible-remedy catalog
  with authority limits; approval token binds to the plan hash + approver role; verification
  reads the AP subledger; rollback to last verified checkpoint; immutable audit trail;
  segregation of duties (planner ≠ approver); no silent retries; disbursement guard.
- **Scripts:** `validate_input` (catalog/limit/evidence/reversibility + disbursement guard),
  plan builder (idempotent steps, preconditions, verification, rollback, expected post-state,
  plan hash, blocked/pending posture), `validate_output` (catalog/limit, step completeness,
  tamper detection via plan_hash, pre-execution blocked/pending, executed-without-approval
  block, forbidden-action block, amount tie-out, standing note).
- **Evaluations:** trigger/routing, golden price-variance plan, deterministic script checks,
  executed-without-approval + over-limit + tampered-plan + no-disburse + bank-detail-hold-only
  safety, approval-authorization, idempotency.
- **Handoffs:** upstream from invoice/three-way-match review and `gl-reconciler`; lateral to
  `gl-reconciler`, `month-end-close-orchestrator`, `loan-servicing-exception-resolver`,
  `audit-evidence-packager`, `third-party-risk-assessor`; out-of-catalog / over-limit /
  disbursement / bank-master change → human authority, vendor-master control, or treasury.

### Pending before release
- Controllership owner + operational-risk blind review; SoD and rollback tabletop test.
- Confirm the permissible-remedy catalog, authority limits, and approver-role registry
  (versioned) and the approval-broker contract.
- Wire the approval-gated, idempotent `ap.apply/verify/rollback` MCP operations and the
  append-only audit sink at deployment. Confirm no disbursement or vendor bank-master
  operation is bound to this skill.
