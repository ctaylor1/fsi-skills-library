# Changelog — month-end-close-orchestrator

## [0.1.0] — 2026-07-18
Initial authoring in the FSI Skills Library (baseline status: `new`). The Finance &
Operations R4 gated-orchestration skill for period-end close.

- **Scope:** plan → validate → approve → execute → verify → audit for the month-end close —
  coordinating close tasks and dependencies and gating every posting and sign-off (accrual /
  reclass / allocation journals, reconciliation and task certifications, sub-ledger and
  period locks).
- **Controls:** R4; execution is approval-gated and idempotent; permissible close-action
  catalog with posting-authority limits; approval token binds to the plan hash + approver
  role; the plan's required role is the strictest across steps (`controller` for any journal
  or lock, `close-manager` for certifications); verification reads the system of record;
  rollback to last verified checkpoint; immutable audit trail; segregation of duties
  (preparer ≠ approver); no silent retries.
- **Orchestration invariants:** dependency graph must be a DAG (cycles and dangling
  dependencies rejected); tasks topologically ordered into steps; a reconciliation may be
  certified only with zero unresolved breaks; a sub-ledger lock or period close may be
  sequenced/executed only after its prerequisites are verified.
- **Scripts:** `validate_input` (catalog / limit / evidence / reversibility / unresolved-break
  / duplicate-id / cycle checks), plan builder (topological ordering, idempotent steps,
  preconditions, verification, rollback, expected post-state, plan hash, blocked/pending
  posture), `validate_output` (catalog / limit, step completeness, journal tie-out,
  dependency-order enforcement, tamper detection via plan_hash, pre-execution blocked/pending,
  executed-without-approval block, standing note).
- **Evaluations:** trigger/routing, golden close plan (accrual → certify recon → close
  period), deterministic script checks, executed-without-approval + over-limit + un-cleared
  reconciliation + cycle + tampered-plan safety, approval-authorization, idempotency.
- **Handoffs:** upstream from `gl-reconciler`, `transaction-reconciliation-helper`,
  `accounts-payable-exception-resolver`, `financials-normalizer`; downstream to
  `management-reporting-packager`, `fpa-variance-analyzer`,
  `regulatory-reporting-data-validator`, `audit-evidence-packager`,
  `financial-statement-audit-assistant`; out-of-catalog / over-limit / irreversible → human
  authority.

### Pending before release
- Controllership controls owner + operational-risk blind review; SoD and rollback tabletop
  test covering a partial-close rollback.
- Confirm the permissible close-action catalog, posting-authority limits, and approver-role
  registry (versioned) and the approval-broker contract.
- Wire the approval-gated, idempotent `gl.post` / `close.certify` / `subledger.lock` /
  `period.close` / `*.verify` / `*.rollback` MCP operations and the append-only audit sink at
  deployment.
