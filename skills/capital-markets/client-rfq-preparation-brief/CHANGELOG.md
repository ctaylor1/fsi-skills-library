# Changelog — client-rfq-preparation-brief

## [0.1.0] — 2026-07-19
Initial authoring in the FSI Skills Library (baseline status: `new`; 2026 industry-expansion
cohort).

- **Scope:** deterministic RFQ preparation brief — instrument summary, client context, surfaced
  suitability/eligibility flags (KYC status, restricted product, jurisdiction), prior-activity
  summary, and required-section completeness; each flag/gap cited; review-only disposition.
- **Controls:** R3 draft-only; NEVER prices/quotes, makes a firm bid/offer, commits or executes,
  or determines suitability/eligibility (flags are surfaced, not adjudicated); missing client
  context never treated as eligible; client-id masking; `external-delivery` approval; information
  barriers.
- **Scripts:** `validate_input` (rfq + client context + checklist), `calculate_or_transform`
  (assemble + surface flags + completeness), `validate_output` (flag/gap citation coverage,
  review-only disposition, no-pricing/commitment screen, disclaimer).
- **Evaluations:** trigger/routing, golden brief (KYC/restricted/completeness), missing-KYC edge,
  deterministic script checks, no-pricing safety (language + citation) + injection,
  external-delivery authorization.
- **Handoffs:** `pricing-hedging-scenario-calculator`, `trade-idea-evidence-packet`,
  `transaction-cost-estimator`.

### Pending before release
- Capital-markets sales/compliance owner review; suitability-policy flag-rule config sign-off.
- Wire read-only CRM / instrument-reference / prior-activity MCP integrations at deployment.
