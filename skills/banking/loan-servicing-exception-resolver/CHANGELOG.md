# Changelog — loan-servicing-exception-resolver

## [0.1.0] — 2026-07-17
Initial authoring in the FSI Skills Library (baseline status: `new`). The Banking R4
gated-orchestration exemplar.

- **Scope:** plan → validate → approve → execute → verify → audit for servicing exceptions
  (misapplied payment, fee-in-error, escrow miscalc, duplicate payment).
- **Controls:** R4; execution is approval-gated and idempotent; permissible-remedy catalog
  with authority limits; approval token binds to the plan hash + approver role; verification
  reads the system of record; rollback to last verified checkpoint; immutable audit trail;
  segregation of duties (planner ≠ approver); no silent retries.
- **Scripts:** `validate_input` (catalog/limit/evidence/reversibility checks), plan builder
  (idempotent steps, preconditions, verification, rollback, expected post-state, plan hash,
  blocked/pending posture), `validate_output` (catalog/limit, step completeness, tamper
  detection via plan_hash, pre-execution blocked/pending, executed-without-approval block,
  amount tie-out, standing note).
- **Evaluations:** trigger/routing, golden reallocation plan, deterministic script checks,
  executed-without-approval + over-limit + tampered-plan safety, approval-authorization,
  idempotency.
- **Handoffs:** upstream from servicing diagnosis; lateral to
  `accounts-payable-exception-resolver`, `gl-reconciler`, `collections-treatment-planner`,
  `loan-package-completeness-checker`; out-of-catalog/over-limit → human authority.

### Pending before release
- Servicing controls owner + operational-risk blind review; SoD and rollback tabletop test.
- Confirm the permissible-remedy catalog, authority limits, and approver-role registry
  (versioned) and the approval-broker contract.
- Wire the approval-gated, idempotent `servicing.apply/verify/rollback` MCP operations and
  the append-only audit sink at deployment.
