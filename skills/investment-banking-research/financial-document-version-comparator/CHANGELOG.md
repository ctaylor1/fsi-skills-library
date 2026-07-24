# Changelog — financial-document-version-comparator

## [0.1.0] — 2026-07-19
Initial authoring in the FSI Skills Library (baseline status: `new`; 2026 industry-expansion
cohort).

- **Scope:** deterministic structural diff of two versions of the same document — added/removed
  sections, normalized text changes, and changed data values — each located and cited; review-
  only disposition.
- **Controls:** R2 read-only; NEVER judges legal significance/materiality/disclosure sufficiency,
  approves/edits/publishes a version, or compares different doc_ids; text normalization suppresses
  whitespace/case-only noise; `external-delivery` approval; MNPI / information-barrier handling.
- **Scripts:** `validate_input` (two versions, same doc_id), `calculate_or_transform` (deterministic
  diff), `validate_output` (change-location + citation coverage, review-only disposition,
  no-significance/approval screen, disclaimer).
- **Evaluations:** trigger/routing, golden diff (with whitespace-noise suppression), doc_id-mismatch
  edge, deterministic script checks, no-significance safety + injection, external-delivery authorization.
- **Handoffs:** `contract-obligation-extractor`, `communications-compliance-reviewer`,
  `policy-wording-comparator`.

### Pending before release
- Deal-execution / document-control owner review; structured-extraction mapping sign-off.
- Wire read-only document-repository + document-intelligence MCP integrations at deployment.
