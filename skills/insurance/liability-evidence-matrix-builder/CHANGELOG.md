# Changelog — liability-evidence-matrix-builder

## [0.1.0] — 2026-07-19
Initial authoring in the FSI Skills Library (baseline status: `new`; 2026 industry-expansion
cohort).

- **Scope:** deterministic fact→evidence matrix — supporting/contradicting evidence per alleged
  fact, coverage status (supported/contested/unsupported), and gap flags (unsupported facts,
  dangling evidence references); each cell cited; review-only disposition.
- **Controls:** R3 read-only; NEVER determines liability/fault/negligence, apportions
  responsibility, or decides the claim; contested evidence is surfaced, never resolved; bare facts
  never inferred as supported; `external-delivery` approval; NPI/PII (incl. injury/medical) masking.
- **Scripts:** `validate_input` (facts + evidence + reference lists), `calculate_or_transform`
  (map + status + gaps), `validate_output` (evidence-cell citation coverage, review-only
  disposition, no-liability screen, disclaimer).
- **Evaluations:** trigger/routing, golden matrix (supported/contested/unsupported + dangling),
  all-supported edge, deterministic script checks, no-liability safety (language + citation) +
  injection, external-delivery authorization.
- **Handoffs:** `claim-damage-evaluation-comparator`, `claim-settlement-authority-packet`,
  `fnol-normalizer`.

### Pending before release
- Claims owner review; status-threshold and evidence-taxonomy sign-off.
- Wire read-only claim fact/evidence-store MCP integrations at deployment.
