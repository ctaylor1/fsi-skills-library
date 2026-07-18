# Changelog — scenario-sensitivity-generator

## [0.1.0] — 2026-07-18
Initial authoring in the FSI Skills Library (baseline status: `new`).

- **Scope:** deterministic scenarios, one-/two-way sensitivities, breakevens (bisection),
  and decision thresholds over a supplied base-case model; draft-only exhibit for review.
- **Controls:** R2; no recommendation/rating/price target/fairness opinion; whitelisted
  formula grammar; driver provenance required; reproducibility via `config_version`;
  MNPI / information-barrier handling; `external-delivery` approval.
- **Scripts:** `validate_input` (model/formula/provenance schema), `calculate_or_transform`
  (deterministic recompute + bisection), `validate_output` (independent tie-out re-derivation,
  breakeven-plug-back, no-advice screen, disclaimer).
- **Evaluations:** trigger/routing, golden pack, deterministic script checks, no-advice
  safety + injection, external-delivery authorization.
- **Handoffs:** upstream `dcf-modeler` / `three-statement-model-builder` / `lbo-model-builder`
  / `merger-model-builder` / `comps-analysis-builder`; downstream `investment-banking-pitch-builder`
  / `company-profile-builder` / `due-diligence-packager`; lateral `market-sizing-builder`.

### Pending before release
- Domain SME (modeling) blind review; MNPI / information-barrier control review.
- Wire read-only model/market-data/config MCP integrations at deployment.
