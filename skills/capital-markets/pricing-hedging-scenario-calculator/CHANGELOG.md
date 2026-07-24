# Changelog — pricing-hedging-scenario-calculator

## [0.1.0] — 2026-07-19
Initial authoring in the FSI Skills Library (baseline status: `new`; 2026 industry-expansion
cohort).

- **Scope:** deterministic linear (DV01) scenario worksheet — per-scenario illustrative P&L,
  delta-neutral hedge units and side, and residual DV01 after hedging; parameters recorded;
  linear-approximation limitation stated.
- **Controls:** R3 model-and-calculate; NEVER states a firm price/quote/bid/offer and NEVER
  executes/puts on/instructs a trade or hedge; no assumed risk parameter; no dividing by a zero
  hedge DV01; linear estimate never presented as exact for convex/optioned positions;
  `external-delivery` approval; information barriers.
- **Scripts:** `validate_input` (DV01 + direction + scenarios + hedge DV01),
  `calculate_or_transform` (scenario P&L + hedge sizing), `validate_output` (P&L identity + hedge
  tie, no-firm-price/execution screen, disclaimer).
- **Evaluations:** trigger/routing, golden scenarios (P&L + hedge sizing), zero-hedge-DV01 edge,
  deterministic script checks, no-firm-price safety (language + P&L tie) + injection,
  external-delivery authorization.
- **Handoffs:** `transaction-cost-estimator`, `client-rfq-preparation-brief`, `trade-break-resolver`.

### Pending before release
- Capital-markets structuring/risk owner review; DV01-convention and non-linear-escalation sign-off.
- Wire read-only risk-system / hedge-reference MCP integrations at deployment.
