# Changelog — model-roll-forward-auditor

## [0.1.0] — 2026-07-19
Initial authoring in the FSI Skills Library (baseline status: `new`; 2026 industry-expansion
cohort).

- **Scope:** deterministic roll-forward continuity audit — per line item, residual =
  current_opening − prior_ending with a tolerance-based tie/break flag, plus structural-break
  detection (item present in one version only); each break cited; review-only disposition.
- **Controls:** R2 model-and-calculate; checks continuity ONLY — NEVER opines on valuation/fair
  value, approves/validates the model, or confirms correctness; missing balances never assumed
  continuous; tolerance never invented (default exact match, stated); MNPI/information-barrier
  controls; `external-delivery` approval.
- **Scripts:** `validate_input` (numeric prior/current balances), `calculate_or_transform`
  (residual + tie/break), `validate_output` (residual identity, review-only disposition,
  no-valuation/approval screen, disclaimer).
- **Evaluations:** trigger/routing, golden audit (tie/break/tolerance), structural-break edge,
  deterministic script checks, no-valuation safety (language + residual tie) + injection,
  external-delivery authorization.
- **Handoffs:** `financial-document-version-comparator`, `capital-structure-maturity-mapper`,
  `research-publication-preparation-assistant`.

### Pending before release
- IB/deal-execution owner review; tolerance-convention and line-item-mapping sign-off.
- Wire read-only model-version-store MCP integrations at deployment.
