# Changelog — stablecoin-payment-controls-reviewer

## [0.1.0] — 2026-07-17
Initial authoring in the FSI Skills Library (baseline status: `new`). R3 decision-support:
evidences control findings and recommends; a human adjudicates.

- **Scope:** evaluate a stablecoin payment/settlement program's controls across reserve,
  custody, screening, transaction, operational, reconciliation, and disclosure categories;
  produce cited findings (`pass`/`fail`/`gap`/`not_evaluable`), per-category coverage, and a
  suggested review disposition. Read-only; no approval, attestation, closure, or filing.
- **Control engine (deterministic):** 18-control catalog with per-control rules; explainable
  findings + evidence citations; deterministic disposition mapping (Controls Evidenced /
  Findings - Remediation Recommended / Material Gaps - Escalate) with a critical-control
  fail-closed escalation (see `scripts/calculate_or_transform.py`,
  `references/domain-rules.md`).
- **Controls:** R3; hard boundary against launch approval, compliance determination/
  attestation, sanctions/AML findings, case closure, and filing/system-of-record writes;
  versioned-config thresholds only; `required` human adjudication.
- **Scripts:** `validate_input` (attestation schema, evaluability + missing-critical
  warnings), the control engine, `validate_output` (finding/citation completeness,
  deterministic disposition tie-out, prohibited decision/closure/filing language screen,
  disclaimer, remediation prompts).
- **Evaluations:** trigger/routing, golden Escalate case, unattested-critical edge,
  deterministic script checks, fail-closed safety on a non-compliant pack, prompt-injection,
  and R3 authorization (no autonomous decision/closure/write).
- **Handoffs:** downstream to `sanctions-match-adjudicator`, `aml-alert-triager`,
  `transaction-monitoring-alert-investigator`, `suspicious-activity-report-drafter`,
  `settlement-break-reconciler`, `transaction-reconciliation-helper`, `gl-reconciler`,
  `payment-failure-diagnoser`, `payment-exception-investigator`, `payment-repair-assistant`,
  `iso-20022-message-interpreter`, `third-party-risk-assessor`,
  `regulatory-reporting-data-validator`, `regulatory-change-impact-analyzer`,
  `network-rules-change-tracker`, `audit-evidence-packager`,
  `regulatory-exam-response-packager`.

### Pending before release
- Domain SME (payments risk/compliance) + control-owner blind review; legal review of the
  regulatory framing (GENIUS Act / MiCA / NYDFS / FATF).
- Confirm the versioned threshold/disposition config source, its owner, and jurisdiction
  packs.
- Wire read-only MCP integrations (attestations, custody/trust agreements, screening/risk
  config, settlement/reconciliation reports, disclosures, config) at deployment.
