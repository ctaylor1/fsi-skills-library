# Changelog — trade-break-resolver

## [Unreleased] — guardrail hardening (`validate_output`)
Adversarial pre-commit review fixes; no change to the plan/execution data contract.

- **plan_hash fails closed:** a non-rejected plan with a missing or blank `plan_hash` is now
  rejected (previously the tamper check was skipped when the hash was absent, failing OPEN).
  Fixture: `evals/files/plan_missing_hash.json`.
- **Authority limit from the catalog:** the amount is validated against the permissible-repair
  **catalog** limit for the break type (read from the same `validate_input.CATALOG` the engine
  uses), not the plan's self-declared `authority_limit`; a plan can no longer inflate its own
  limit to bypass the gate. Fixtures: `evals/files/plan_over_catalog_limit.json` (bypass now
  blocked) and `evals/files/plan_catalog_limit_ok.json` (limit correctly sourced from catalog).
- **Approver-role enforcement:** an executed plan is rejected unless the approver's role matches
  the catalog-required approver role for the break type (previously only status/token/approver
  presence were checked, so a wrong-role approval passed). Fixture:
  `evals/files/plan_wrong_role.json`.

## [0.1.0] — 2026-07-18
Initial authoring in the FSI Skills Library (baseline status: `new`). The Capital Markets R4
gated-orchestration package, mirroring the Banking exemplar
`loan-servicing-exception-resolver`.

- **Scope:** plan → validate → approve → execute → verify → audit for trade breaks
  (mis-booked account, quantity mismatch, price mismatch, duplicate booking).
- **Controls:** R4; execution is approval-gated and idempotent; permissible-repair catalog
  with authority limits; approval token binds to the plan hash + approver role; verification
  reads the firm OMS/EMS (system of record); counterparty/clearing records are reference-only,
  never written; rollback to last verified checkpoint; immutable audit trail; segregation of
  duties (planner ≠ approver); no silent retries.
- **Scripts:** `validate_input` (catalog/limit/evidence/reversibility + rebook-source checks),
  plan builder (idempotent steps, preconditions, verification, rollback, expected post-state,
  plan hash, blocked/pending posture), `validate_output` (catalog/limit, step completeness,
  tamper detection via plan_hash, pre-execution blocked/pending, executed-without-approval
  block, amount tie-out, standing note).
- **Evaluations:** trigger/routing, golden rebook plan, deterministic script checks,
  executed-without-approval + over-limit + tampered-plan safety, approval-authorization,
  idempotency.
- **Handoffs:** upstream from `post-trade-settlement-monitor` / `trade-confirmation-explainer`;
  lateral to `transaction-reporting-quality-checker`, `best-execution-reviewer`,
  `market-surveillance-alert-investigator`, `corporate-action-interpreter`,
  `margin-collateral-optimizer`; out-of-catalog/over-limit → human authority (desk supervisor /
  trade control).

### Pending before release
- Trade-support controls owner + operational-risk blind review; SoD and rollback tabletop test.
- Confirm the permissible-repair catalog, authority limits, and approver-role registry
  (versioned) and the approval-broker contract.
- Wire the approval-gated, idempotent `oms.apply/verify/rollback` MCP operations and the
  append-only audit sink at deployment.
