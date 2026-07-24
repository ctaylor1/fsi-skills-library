# Changelog — insurance-rating-quote-worksheet

## [0.1.0] — 2026-07-19
Initial authoring in the FSI Skills Library (baseline status: `new`; 2026 industry-expansion
cohort).

- **Scope:** deterministic premium buildup — per coverage, base rate × ordered rating factors
  (with a step trail), explicit minimum-premium application, fees, and a total across coverages +
  policy fees; auditable indicated-premium worksheet.
- **Controls:** R3 model-and-calculate; NEVER binds coverage, issues/finalizes a quote, or makes
  an offer; never overrides the rate manual or invents a factor; minimum premium shown as an
  explicit step; `external-delivery` approval; NPI/PII masking.
- **Scripts:** `validate_input` (base rates + factors + coverages), `calculate_or_transform`
  (buildup + min + totals), `validate_output` (factor-product tie + total tie, no-bind/quote
  screen, disclaimer).
- **Evaluations:** trigger/routing, golden rating (buildup/min/fees/total), min-premium edge,
  deterministic script checks, no-bind safety (language + tie) + injection, external-delivery
  authorization.
- **Handoffs:** `insurance-regulatory-filing-packager`, `actuarial-model-run-assistant`.

### Pending before release
- Underwriting owner review; rate-manual factor-mapping and minimum-premium convention sign-off.
- Wire read-only rate-manual/rating-factor + risk-characteristic MCP integrations at deployment.
