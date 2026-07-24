# Changelog — capital-structure-maturity-mapper

## [0.1.0] — 2026-07-19
Initial authoring in the FSI Skills Library (baseline status: `new`; 2026 industry-expansion
cohort).

- **Scope:** deterministic capital-structure & maturity map — totals by seniority/type,
  secured-unsecured split, maturity wall by year, weighted-average maturity and coupon, and
  near-term (≤24m) maturities — each tied to source lines; descriptive packaging.
- **Controls:** R2 draft-only; descriptive ONLY — NEVER gives financing advice/recommendations,
  ranks/labels a structure, or suggests a transaction; never sums mixed currencies without a
  supplied FX basis; MNPI/information-barrier controls; `external-delivery` approval.
- **Scripts:** `validate_input` (instruments + as_of + currency check), `calculate_or_transform`
  (buckets + weighted averages + wall), `validate_output` (bucket tie-outs, no-advice screen,
  disclaimer).
- **Evaluations:** trigger/routing, golden map (buckets/wall/near-term/weighted averages),
  mixed-currency edge, deterministic script checks, no-advice safety (language + tie) + injection,
  external-delivery authorization.
- **Handoffs:** `financing-alternatives-calculator`, `credit-terms-covenant-extractor`,
  `covenant-compliance-monitor`.

### Pending before release
- IB/DCM owner review; instrument-taxonomy and currency-handling sign-off; MNPI-barrier configuration.
- Wire read-only debt-schedule/reference-data MCP integrations at deployment.
