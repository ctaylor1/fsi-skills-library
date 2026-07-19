# Changelog — employee-trading-preclearance-assistant

## [0.1.0] — 2026-07-17
Initial authoring in the FSI Skills Library (baseline status: `new`). The Compliance &
Financial Crime R4 gated-orchestration skill for employee personal-trade preclearance.

- **Scope:** plan → validate → approve → execute → verify → audit for an employee
  personal-account trade preclearance decision (`approve` / `approve_with_conditions` / `deny`).
- **Controls:** R4; execution is approval-gated and idempotent; mandatory screens (restricted
  list, watch list, blackout, minimum-holding, conflicts/MNPI) must be performed before
  planning; hard blocks force a `deny` (an `approve*` plan for a hard-blocked request fails
  closed); notional authority limits with CCO escalation above the senior limit; approval token
  binds to the plan hash + approver role; segregation of duties (approver ≠ requesting
  employee); time-boxed, scoped clearance; verification reads the preclearance register;
  rollback to the last verified checkpoint; immutable audit trail; no investment advice; no
  silent retries.
- **Scripts:** `validate_input` (structure + mandatory-screen completeness, fail closed),
  plan builder (deterministic decision derivation, idempotent steps with preconditions,
  verification, rollback, expected post-state, plan hash, blocked/pending posture),
  `validate_output` (decision permissibility vs hard blocks, notional-in-limit, approver-role
  match, step completeness, clearance/notional tie-out, deny-issues-no-clearance, tamper
  detection via plan_hash, pre-execution blocked/pending, executed-without-approval and
  approver-equals-employee blocks).
- **Evaluations:** trigger/routing, golden approve plan, deterministic script checks (approve,
  hard-block deny), executed-without-approval + over-limit + tampered-plan + hard-block
  fail-closed safety, segregation-of-duties authorization, idempotency.
- **Handoffs:** upstream from personal-trade intake and `conflicts-of-interest-reviewer`;
  lateral to `surveillance-alert-triager`, `market-surveillance-alert-investigator`,
  `sanctions-match-adjudicator`, `transaction-monitoring-alert-investigator`,
  `mandate-compliance-monitor`; over-limit/override → Chief Compliance Officer.

### Pending before release
- Compliance controls owner + operational-risk blind review; SoD and rollback tabletop test.
- Confirm the versioned personal-trading policy, restricted/watch lists, blackout calendars,
  minimum-holding period, and the decision-authority matrix (approver roles + notional limits).
- Wire the approval-gated, idempotent `preclearance.record_decision/issue_clearance/verify/
  rollback` MCP operations, the screen-evaluation service, and the append-only audit sink at
  deployment.
