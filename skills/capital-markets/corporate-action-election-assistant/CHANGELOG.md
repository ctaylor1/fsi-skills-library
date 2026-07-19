# Changelog — corporate-action-election-assistant

## [0.1.0] — 2026-07-17
Initial authoring in the FSI Skills Library (baseline status: `new`). The Capital Markets R4
gated-orchestration skill for voluntary corporate-action elections.

- **Scope:** plan → validate → approve → submit → verify → audit for voluntary elections
  (tender, exchange, optional/scrip dividend, rights subscription, conversion).
- **Controls:** R4; submission is approval-gated and idempotent; permissible-election catalog
  with quantity basis, oversubscription cap, and notional authority limits; approval token
  binds to the plan hash + approver role; verification reads the custodian/agent
  acknowledgment; rollback withdraws/supersedes before the deadline; immutable audit trail;
  segregation of duties (planner ≠ approver); no silent retries; no option or tax advice.
- **Scripts:** `validate_input` (catalog/option/basis/over-election/notional-limit/
  reversibility/deadline/evidence checks), plan builder (idempotent legs, preconditions,
  verification, rollback, expected post-state, plan hash, blocked/pending posture, self-check),
  `validate_output` (catalog/option, quantity tie-out, over-election, notional limit + tie,
  in-window, step completeness, tamper detection via plan_hash, pre-submission blocked/pending,
  submitted-without-approval block, standing note).
- **Evaluations:** trigger/routing (interpret / settlement / break), golden optional-dividend
  election plan, deterministic script checks, submitted-without-approval + over-eligible +
  past-deadline + tampered-plan safety, no-advice, approval-authorization, idempotency.
- **Handoffs:** upstream from `corporate-action-interpreter` and `portfolio-holdings-summarizer`;
  lateral to `post-trade-settlement-monitor`, `transaction-reporting-quality-checker`,
  `trade-break-resolver`; off-catalog/over-limit/past-cutoff/irreversible and option/tax advice
  → human authority (operations, licensed representative, tax professional).

### Pending before release
- Corporate-actions controls owner + operational-risk blind review; SoD and rollback tabletop
  test (withdraw/supersede before deadline).
- Confirm the permissible-election catalog, per-event caps, notional authority limits, and
  approver-role registry (versioned) and the approval-broker contract.
- Wire the approval-gated, idempotent `election.submit/verify/withdraw` MCP operations, the
  custody/agent read operations, and the append-only audit sink at deployment.
