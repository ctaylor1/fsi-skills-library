# Changelog — regulatory-reporting-data-validator

## [0.1.0] — 2026-07-18
Initial authoring in the FSI Skills Library (baseline status: `new`).

- **Scope:** deterministic, explainable validation of a regulatory-report package —
  completeness, lineage, edit-checks/internal-consistency, source reconciliation tie-outs,
  range/sign bounds, sign-off completeness, segregation of duties, timeliness, and
  variance-vs-prior — with cited evidence and a deterministic filing-readiness band
  (`Blocked` / `Review` / `Clear`). Read-only; no certification, sign-off, filing, or GL
  correction.
- **Checks (deterministic):** eight blocking checks + two advisory checks, each explainable
  and evidenced (see `scripts/calculate_or_transform.py` and `references/domain-rules.md`).
- **Controls:** R2; hard boundary against filing determination, certification/attestation,
  sign-off, submission/transmission, and GL posting; versioned-config thresholds/tolerances
  only (never loosened to clear an exception); remediation prompts required;
  `external-delivery` approval.
- **Scripts:** `validate_input` (package schema, evaluability warnings), the check engine,
  `validate_output` (evidence/citation completeness, deterministic readiness tie-out,
  certification/filing-language screen, disclaimer, remediation prompts).
- **Evaluations:** trigger/routing, golden `Blocked` case, no-prior-period edge, deterministic
  script checks, fail-closed safety on a non-compliant fixture + injection, external-delivery
  authorization.
- **Handoffs:** upstream `gl-reconciler`, `financials-normalizer`,
  `month-end-close-orchestrator`; downstream `gl-reconciler`,
  `management-reporting-packager`, `audit-evidence-packager`,
  `financial-statement-audit-assistant`, `regulatory-exam-response-packager`,
  `transaction-reporting-quality-checker`.

### Pending before release
- Domain SME (regulatory-reporting control owner) + control-owner blind review.
- Confirm the versioned threshold/tolerance/required-role config source and its owner, and
  the reporting-instruction (edit-check/cell/due-date) spec version per report code.
- Wire read-only MCP integrations (ERP/GL, subledger, consolidation, FP&A/prior filings,
  sign-off workflow, config) at deployment.
