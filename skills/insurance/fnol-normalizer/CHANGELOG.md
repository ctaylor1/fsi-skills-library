# Changelog — fnol-normalizer

## [0.1.0] — 2026-07-19
Initial authoring in the FSI Skills Library (baseline status: `new`; 2026 industry-expansion
cohort).

- **Scope:** deterministic FNOL intake normalization — controlled-vocabulary mapping of
  loss_type/cause, required-field presence, and loss/report date-order checks — producing a
  normalized record + cited exceptions; review-only disposition.
- **Controls:** R3 read-only; NEVER determines coverage, assigns liability/fault, sets a reserve,
  or opens/routes/adjudicates a claim; unmappable codes flagged (never guessed); `external-delivery`
  approval; NPI/PII masking.
- **Scripts:** `validate_input` (raw record + vocab config), `calculate_or_transform` (map +
  carry-through + flag), `validate_output` (exception citation coverage, review-only disposition,
  no-adjudication screen, disclaimer).
- **Evaluations:** trigger/routing, golden normalization (map + unmapped + missing-required),
  date-order edge, deterministic script checks, no-adjudication safety + injection, external-delivery
  authorization.
- **Handoffs:** `claim-damage-evaluation-comparator`, `liability-evidence-matrix-builder`.

### Pending before release
- Claims-intake owner review; controlled-vocabulary and required-fields config sign-off.
- Wire read-only claims-intake + vocabulary-config MCP integrations at deployment.
