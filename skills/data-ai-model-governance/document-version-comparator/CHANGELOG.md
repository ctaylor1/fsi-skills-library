# Changelog — document-version-comparator

##0.2.0 —2026-10-20

- Phase1 critical input/evidence/partial-state repairs; see native contract.
- Full detached-original reconstruction rejects tampered, omitted and extra result fields; CLI requires --input.
- Strict shapes, calendar dates and finite financial values; supplied-only, unverified permissions/source truth and deployment acceptance limits remain explicit.
- Refreshed native golden result and executable commands; independent adverse-case suite in tools/test_ir_company_phase1.py. No new research engine, live connector or action authority.

# Changelog — document-version-comparator

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

## 2026-09-20 — Category ownership migration

- Moved from Investment Banking & Research to Investment Research; stable skill ID retained.
- Native method and information/publication controls unchanged. Path alias is registered.
