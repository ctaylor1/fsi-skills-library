# Changelog — scenario-sensitivity-generator

## 0.2.0 — 2026-10-20

- Forward-review corrections: same-sign bisection endpoints report not-bracketed/unknown interior roots, not absence of crossings. Reject identical two-way sensitivity axes. Executable evals use python3 -B for standalone portability.

- Require detached original input for native output validation; reconstruct every result and reject omissions, alterations and extra fields. Guard finite numbers, shapes, dates, domains and duplicates; validate before computation.
- This engine evaluates a supplied arithmetic graph only. It has no native three-statement, DCF or credit-runner adapter and cannot establish economic coherence, financing feasibility, calibrated scenario probabilities or full instrument repricing. Model formulas must be mapped and independently checked before reuse; a model_id alone does not prove integration. Invalid/non-finite formulas and unsupported argument shapes fail explicitly.
- Regenerate synthetic positive and adversarial fixtures. Passing checks is not source authentication, professional acceptance or independent institutional assurance.


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

## 2026-09-20 — Category ownership migration

- Moved from Investment Banking & Research to Investment Research; stable skill ID retained.
- Native method and information/publication controls unchanged. Path alias is registered.

## 0.3.0 — 2026-10-20

Phase2 mode engine dcf-forecast performs an actual locally bundled DCF rerun using the full retained base_input and explicit wacc,terminal_growth or bridge overrides. Each scenario is independently revalidated and recomputed. Outer and base model contexts must match exactly. It does not rerun integrated operating assumptions or claim to be a general model engine.
