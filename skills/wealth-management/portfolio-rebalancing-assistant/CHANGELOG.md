# Changelog — portfolio-rebalancing-assistant

## [0.1.0] — 2026-07-17
Initial authoring in the FSI Skills Library (baseline status: `new`). Wealth Management R4
gated-orchestration skill, mirroring the Banking exemplar `loan-servicing-exception-resolver`.

- **Scope:** plan → validate → authorize → execute → verify → audit for a portfolio
  rebalance — measure drift from the target model, assess tax (realized short-/long-term gain,
  wash sale), liquidity/funding, restriction, concentration, turnover, and cost impacts, and
  stage a proposed buy/sell trade list.
- **Controls:** R4; execution is approval-gated and idempotent; **two-party** authorization
  (advisor AND client) with tokens bound to the plan hash; permissible-action policy with
  per-order authority limit, turnover ceiling, short-term-gain budget, concentration cap, and
  drift band; verification reads OMS fills/weights; rollback (cancel/offset) to last verified
  checkpoint; immutable audit trail; segregation of duties (planner ≠ approvers); no silent
  retries; no personalized investment or tax advice.
- **Scripts:** `validate_input` (permissible-action/limit/restriction/wash-sale/gain-budget/
  turnover/funding checks), plan builder (idempotent steps, preconditions, verification,
  rollback, expected post-state, compliance summary, plan hash, blocked/pending posture),
  `validate_output` (permissible/in-limit, step completeness, compliance clean, amount
  tie-out, plan_hash tamper detection, pre-execution blocked/pending, executed-without-both-
  tokens block).
- **Evaluations:** trigger/routing, golden rebalance plan, deterministic script checks,
  executed-without-approval + over-limit + restricted-buy + wash-sale + tampered-plan safety,
  two-party authorization, idempotency.
- **Handoffs:** upstream from IPS/holdings/exposure/drift analysis; lateral to
  `suitability-reg-bi-reviewer`, `senior-investor-protection-screener`,
  `employee-trading-preclearance-assistant`, `best-execution-reviewer`,
  `post-trade-settlement-monitor`, `mandate-compliance-monitor`, `advisor-follow-up-assistant`;
  out-of-limit/restricted/tax-advice → human trading desk / compliance / licensed advisor.

### Pending before release
- Wealth advisory + compliance owner and operational-risk blind review; SoD, two-party
  authorization, and rollback tabletop test.
- Confirm the versioned target-model/IPS, restrictions/mandate list, approved tax-assumption
  set, authority limits, and the two-party approval-broker contract.
- Wire the approval-gated, idempotent `oms.submit/verify/cancel_or_reverse` MCP operations and
  the append-only audit sink at deployment.
