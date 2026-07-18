# Changelog — coverage-initiation-researcher

## [0.1.0] — 2026-07-17
Initial authoring in the FSI Skills Library (baseline status: `new`). A multi-step domain
workflow that assembles an initiating-coverage research draft and grades it against a
deterministic readiness check.

- **Scope:** assemble + grade an initiating-coverage draft (business model, industry,
  competitive position, forecast, catalysts, risks, valuation, thesis) with cited evidence,
  a draft valuation range, and a readiness band. Read-only; DRAFT only.
- **Deterministic core (`scripts/calculate_or_transform.py`):** section completeness +
  evidence coverage, forecast internal-consistency checks (growth tie-out, margin bounds,
  ascending years), draft valuation triangulation (range + weighted midpoint), and the
  deterministic readiness mapping.
- **Controls:** R2; hard boundary against personalized investment advice, approved
  rating/price target, guarantee/certainty language, and MNPI in the draft; proposed rating
  stays `draft-unapproved`; `external-delivery` approval by supervisory analyst + research
  committee before publication.
- **Scripts:** `validate_input` (dossier schema, completeness/evaluability warnings), the
  assembly engine, `validate_output` (section/evidence completeness, deterministic readiness
  tie-out, valuation completeness, advice/decision-language screen, MNPI attestation,
  disclaimer + DRAFT banner).
- **Evaluations:** trigger/routing, golden "Ready for supervisory review" case, missing-section
  edge, deterministic script checks, no-advice safety fixture that fails closed + injection,
  external-delivery authorization.
- **Handoffs:** components `three-statement-model-builder`, `dcf-modeler`,
  `comps-analysis-builder`, `scenario-sensitivity-generator`, `market-sizing-builder`,
  `market-landscape-researcher`, `company-profile-builder`, `earnings-results-analyzer`;
  downstream `coverage-meeting-preparer`; rating/price-target/publication to supervisory
  analyst + research committee (human).

### Pending before release
- Domain SME (research supervisory) + control-owner blind review; independence/disclosure
  and MNPI-wall review by compliance.
- Confirm the versioned coverage config (required sections, tolerances, readiness mapping)
  source and its owner.
- Wire read-only MCP integrations (filings, market data, research corpus, model artifacts,
  config) at deployment.
