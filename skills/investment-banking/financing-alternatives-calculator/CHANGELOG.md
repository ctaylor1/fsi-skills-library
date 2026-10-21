# Changelog — financing-alternatives-calculator

## [0.1.0] — 2026-07-19
Initial authoring in the FSI Skills Library (baseline status: `new`; 2026 industry-expansion
cohort).

- **Scope:** deterministic financing-cost comparison across documented alternatives — annual
  interest, amortized upfront fees, all-in annual cost, effective cost rate, total cost over
  term, and (equity) shares issued + dilution; one row per alternative; factual worksheet.
- **Controls:** R2 model-and-calculate; numbers ONLY — NEVER recommends, ranks, or labels an
  option cheapest/best/optimal, and never advises which to choose; missing terms mark metrics
  not-computable (no assumed market rate); MNPI/information-barrier controls; `external-delivery`
  approval.
- **Scripts:** `validate_input` (amount + per-alt terms), `calculate_or_transform` (debt + equity
  metrics), `validate_output` (per-row cost tie-outs, no-recommendation screen, disclaimer).
- **Evaluations:** trigger/routing, golden compare (debt + equity math), missing-term edge,
  deterministic script checks, no-recommendation safety (language + tie) + injection,
  external-delivery authorization.
- **Handoffs:** `capital-structure-maturity-mapper`, `pricing-hedging-scenario-calculator`,
  `market-window-readiness-pack`.

### Pending before release
- IB/DCM/ECM owner review; cost-convention (fee amortization) sign-off.
- Wire read-only documented-terms / reference-data MCP integrations at deployment.

## 2026-09-20 — Category ownership migration

- Moved from Investment Banking & Research to Investment Banking; stable skill ID retained.
- Native method and information/publication controls unchanged. Path alias is registered.
