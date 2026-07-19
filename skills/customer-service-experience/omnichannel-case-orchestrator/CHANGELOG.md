# Changelog — omnichannel-case-orchestrator

## [0.1.0] — 2026-07-17
Initial authoring in the FSI Skills Library (baseline status: `new`). The Customer Service &
Experience R4 gated-orchestration skill.

- **Scope:** unify cross-channel history and run plan → validate → approve → execute → verify
  → audit across case/CRM/billing/comms for a confirmed service case; coordinated actions are
  fee adjustment, goodwill credit, billing refund, account change, and outbound commitment.
- **Controls:** R4; execution is approval-gated and idempotent; permissible-action catalog
  with per-action authority limits and a plan authority cap; approval token binds to the plan
  hash + most-senior required approver role; verification reads the systems of record;
  rollback to last verified checkpoint; immutable audit trail; segregation of duties
  (planner ≠ approver); non-monetary actions are still gated; no silent retries.
- **Scripts:** `validate_input` (catalog/limit/cap/evidence/reversibility checks, unique
  action ids), plan builder (idempotent multi-action steps, preconditions, verification,
  rollback, expected post-state, plan hash, required-role derivation, blocked/pending
  posture), `validate_output` (catalog/limit, plan-cap, step completeness, monetary tie-out,
  tamper detection via plan_hash, pre-execution blocked/pending, executed-without-approval
  block, approver-role match, standing note).
- **Evaluations:** trigger/routing, golden multi-action plan, deterministic script checks,
  executed-without-approval + over-limit + over-cap + tampered-plan + missing-rollback safety,
  approval-authorization (approver role match), idempotency.
- **Handoffs:** upstream from `customer-interaction-summarizer`, `complaint-resolution-assistant`,
  `next-best-action-assistant`, `service-recovery-assistant`, `knowledge-answer-composer`;
  lateral to `dispute-operations-assistant`, `chargeback-dispute-packager`,
  `payment-exception-investigator`, `payment-repair-assistant`,
  `loan-servicing-exception-resolver`, `fee-and-charge-reviewer`,
  `kyc-customer-due-diligence-screener`, `vulnerable-customer-support-assistant`,
  `call-quality-compliance-reviewer`; out-of-catalog/over-limit/over-cap/irreversible →
  human authority.

### Pending before release
- Customer-service controls owner + operational-risk blind review; SoD and rollback tabletop
  test across case/CRM/billing/comms.
- Confirm the permissible-action catalog, per-action limits, plan authority cap, goodwill
  matrix, approved outbound templates, and approver-role registry (versioned), plus the
  approval-broker contract.
- Wire the approval-gated, idempotent `billing.apply` / `crm.apply` / `comms.send` /
  `case.verify` / `case.rollback` MCP operations and the append-only audit sink at deployment.
