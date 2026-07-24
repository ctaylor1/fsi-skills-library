# Changelog — research-publication-preparation-assistant

## [0.1.0] — 2026-07-19
Initial authoring in the FSI Skills Library (baseline status: `new`; 2026 industry-expansion
cohort).

- **Scope:** deterministic pre-publication checks — required-disclosure completeness, rating-scale
  validity, rating/target directional consistency, restricted-list status (hard stop), and
  pre-publication checklist completeness; each gap/flag cited; review-only disposition.
- **Controls:** R3 draft-only; NEVER publishes/distributes, approves for publication, or
  sets/determines/changes the rating or target; restricted ticker is a hard stop (never cleared);
  missing disclosures never assumed present; research-independence + MNPI/information-barrier
  controls; `external-delivery` approval.
- **Scripts:** `validate_input` (note + configs), `calculate_or_transform` (five checks + flags),
  `validate_output` (gap/flag citation coverage, review-only disposition, restricted-hard-stop
  consistency, no-publish/approval/rating screen, disclaimer).
- **Evaluations:** trigger/routing, golden prep (disclosure/consistency/checklist), restricted
  edge, deterministic script checks, no-publish safety (language + citation) + injection,
  external-delivery authorization.
- **Handoffs:** `filing-disclosure-change-detector`, `communications-compliance-reviewer`,
  `earnings-preview-packet-builder`.

### Pending before release
- Research-compliance owner review; disclosure/restricted-list/checklist config and rating-scale
  sign-off.
- Wire read-only note/disclosure/restricted-list/checklist MCP integrations at deployment.
