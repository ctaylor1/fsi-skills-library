# Changelog — margin-collateral-optimizer

## [0.1.0] — 2026-07-17
Initial authoring in the FSI Skills Library (baseline status: `new`).

- **Scope:** explainable, cheapest-to-deliver allocation of eligible collateral to open margin
  calls, with post-haircut coverage, per-call concentration checks, a funding-cost estimate, and
  surfaced shortfalls/breaches. Read-only; recommendation only — no collateral movement, no
  margin-call response, no binding funding decision.
- **Allocation (deterministic):** most-constrained-first call ordering; within a call, post in
  ascending `pledge_cost_bps` then haircut then `asset_id`; concentration cap per asset class per
  call; partial final lot to meet the requirement exactly (see
  `scripts/calculate_or_transform.py`).
- **Controls:** R2; hard boundary against pledging/posting/moving/substituting/settling collateral,
  disputing/accepting/rejecting a margin call, binding funding decisions, and investment advice;
  versioned eligibility/haircut/limit config only; surface-don't-hide on shortfalls and breaches;
  `external-delivery` approval by treasury and operations.
- **Scripts:** `validate_input` (schema, eligibility-gap and coverage-feasibility warnings),
  allocation engine, `validate_output` (citation coverage, per-call coverage tie-out,
  shortfall/breach surfacing, prohibited-language screen, disclaimer, approval gate).
- **Evaluations:** trigger/routing, golden full-coverage case, shortfall edge, deterministic script
  checks, no-execution safety + injection, external-delivery authorization.
- **Handoffs:** downstream to `post-trade-settlement-monitor`, `settlement-break-reconciler`,
  `counterparty-exposure-monitor`, `liquidity-risk-scenario-analyzer`,
  `corporate-action-election-assistant`; execution and margin-call responses are human
  treasury/operations actions in the collateral-management and settlement systems.

### Pending before release
- Domain SME (collateral management / treasury) + control-owner blind review.
- Confirm the versioned eligibility/haircut/limit config source and its owner, and the
  funding-curve (`pledge_cost_bps`) methodology.
- Wire read-only MCP integrations (clearing/CSA schedules, collateral inventory, market/reference
  data, funding curve, limit config) at deployment.
