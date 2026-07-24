# Changelog — trade-idea-evidence-packet

## [0.1.0] — 2026-07-19
Initial authoring in the FSI Skills Library (baseline status: `new`; 2026 industry-expansion
cohort).

- **Scope:** deterministic trade-idea evidence packet — thesis, cited supporting data points,
  risk factors, and surfaced suitability/eligibility flags — with citation-coverage, risk-balance,
  restricted-product (hard stop), general-only, and section-completeness checks; review-only
  disposition.
- **Controls:** R3 draft-only; NEVER recommends to a specific client, determines
  suitability/eligibility, or gives investment advice; uncited claims excluded from evidence (never
  presented as support); restricted product is a hard stop; `external-delivery` approval;
  information barriers; NPI/PII handling.
- **Scripts:** `validate_input` (idea + data points + checklist), `calculate_or_transform`
  (assemble + citation/risk/restricted/section checks), `validate_output` (evidence + gap/flag
  citation coverage, review-only disposition, restricted-hard-stop consistency,
  no-client-recommendation screen, disclaimer).
- **Evaluations:** trigger/routing, golden packet (uncited/general-only/section), restricted edge,
  deterministic script checks, no-client-recommendation safety (language + uncited) + injection,
  external-delivery authorization.
- **Handoffs:** `client-rfq-preparation-brief`, `pricing-hedging-scenario-calculator`,
  `communications-compliance-reviewer`.

### Pending before release
- Capital-markets/research-compliance owner review; suitability-config and restricted-list sign-off.
- Wire read-only market-data/research + suitability-config MCP integrations at deployment.
