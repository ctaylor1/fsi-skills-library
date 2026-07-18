# Changelog — transaction-reporting-quality-checker

## [0.1.0] — 2026-07-17
Initial authoring in the FSI Skills Library (baseline status: `new`). Mirrors the
`account-anomaly-screener` Analyze & review pattern: findings + cited evidence + a
deterministic prohibited-decision screen, with a bad fixture that fails closed.

- **Scope:** deterministic quality-control over regulatory transaction reports —
  completeness, timeliness, identifier validity, mandatory-field population,
  field-mapping/economic reconciliation, and unresolved rejects. Read-only; no determination,
  no report action.
- **Exceptions (deterministic):** `missing_report`, `over_report`, `economic_field_mismatch`
  (blocking); `invalid_identifier`, `missing_required_field`, `late_report`,
  `rejected_report_unresolved` (high); `noncritical_field_mismatch` (low) — each explainable
  and evidenced (see `scripts/calculate_or_transform.py`).
- **Controls:** R2; hard boundary against compliance/breach determination, reportability
  decisions, and report submit/amend/cancel/suppress/self-report; versioned-config thresholds
  only; false-positive checks required; `external-delivery` approval.
- **Scripts:** `validate_input` (batch schema, evaluability warnings), QC engine,
  `validate_output` (evidence/citation completeness, recognized-code check, deterministic
  priority tie-out, determination/action-language screen, disclaimer, false-positive checks).
- **Evaluations:** trigger/routing, golden Blocking case, no-timestamps edge, deterministic
  script checks, no-determination safety + injection, external-delivery authorization.
- **Handoffs:** downstream to `trade-break-resolver`, `regulatory-reporting-data-validator`,
  `market-surveillance-alert-investigator`, `regulatory-exam-response-packager`,
  `best-execution-reviewer`; upstream from `post-trade-settlement-monitor`; report
  submission/amendment/determination reframed as a licensed-human / operations handoff.

### Pending before release
- Domain SME (regulatory reporting control) + control-owner blind review; false-positive /
  false-negative tuning against a labeled production sample.
- Confirm the versioned deadline/required-field/format config source and its owner per regime.
- Wire identifier check-digit validation (ISIN Luhn, LEI mod-97) and the effective
  reference-data snapshot at integration.
- Wire read-only MCP integrations (OMS/EMS, reporting/ARM archive, reference data, config).
