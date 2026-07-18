# Changelog — merger-model-builder

## [0.1.0] — 2026-07-18
Initial authoring in the FSI Skills Library (baseline status: `new`).

- **Scope:** deterministic accretion/dilution and pro forma ownership analysis —
  consideration, financing, synergies, and purchase accounting — as a draft for review.
- **Controls:** R2; no recommendation or fairness opinion; assumptions carry provenance;
  MNPI / information-barrier handling; `external-delivery` approval.
- **Scripts:** `validate_input` (deal/financing/synergy schema), `calculate_or_transform`
  (deterministic model build), `validate_output` (tie-outs, provenance, no-advice screen,
  disclaimer).
- **Evaluations:** trigger/routing, golden model, deterministic script checks,
  non-compliant-output safety + injection, external-delivery authorization.
- **Handoffs:** downstream `scenario-sensitivity-generator` (flex assumptions),
  `investment-banking-pitch-builder` / `company-profile-builder` / `due-diligence-packager`
  (package).

### Pending before release
- Domain SME (M&A) blind review; purchase-accounting assumption review.
- Wire read-only market-data / model MCP integrations at deployment.
