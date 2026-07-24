# Changelog — filing-disclosure-change-detector

## [0.1.0] — 2026-07-20
Initial authoring in the FSI Skills Library (baseline status: `new`; Wave 5 — 2026 industry
expansion). R2 / Analyze & review, read-only.

- **Scope:** deterministic, cited change findings across a prior and current filing/disclosure
  — changed language, new/removed sections and risk factors, restatement/non-reliance wording,
  and exhibit add/change/remove. No materiality, legal-significance, or investment
  determination.
- **Findings (deterministic):** `changed_language` (added/removed spans + similarity ratio),
  `section_added`/`section_removed`, `new_risk_factor`/`removed_risk_factor`,
  `restatement_language` (verbatim marker excerpt), `exhibit_added`/`exhibit_changed`/
  `exhibit_removed` (with `material_contract` flag) — each cited to its version
  (`scripts/calculate_or_transform.py`).
- **Controls:** R2 HARD BOUNDARY against materiality / legal-significance / investment-
  implication determination and restatement conclusions; versioned-config markers/prefixes
  only; deterministic `change_summary` and `review_routing` tie-outs; `external-delivery`
  approval before publication or delivery.
- **Scripts:** `validate_input` (two-version schema, baseline-ordering/alignment checks),
  the change-detection engine, `validate_output` (citation + evidence completeness, summary
  and routing tie-out, prohibited-determination screen, standing disclaimer). Each self-tests
  over a bundled fixture and prints an `N error(s)` line (exit 0 pass / 1 fail).
- **Evaluations:** trigger/routing, golden full-diff (10 findings) vs a bundled fixture,
  deterministic script checks, a no-determination safety fixture that fails closed, an
  injection-resistance behavior, no-exhibits edge, and external-delivery authorization.
- **Handoffs:** downstream to `earnings-results-analyzer`,
  `research-publication-preparation-assistant`, `earnings-preview-packet-builder`,
  `company-profile-builder`, `due-diligence-packager`, `market-landscape-researcher`,
  `regulatory-change-impact-analyzer`.

### Pending before release
- Domain SME (research supervision / disclosure-controls) + control-owner blind review.
- Confirm the versioned marker/prefix config source and its owner; confirm information-barrier
  and restricted-list posture per deployment.
- Wire read-only MCP integrations (filed-form retrieval, document-intelligence, entity
  resolution, config) at deployment.
