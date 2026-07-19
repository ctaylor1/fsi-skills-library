# Changelog — third-party-cyber-risk-reviewer

## [0.1.0] — 2026-07-17
Initial authoring in the FSI Skills Library (baseline status: `new`).

- **Scope:** explainable supplier cyber-risk findings + cited evidence + a suggested
  residual-risk tier for human adjudication. Read-only; no supplier decision, no register
  write.
- **Findings (deterministic):** control_gap, stale_or_missing_attestation,
  open_critical_vulnerabilities, unresolved_material_incident, fourth_party_data_exposure,
  contractual_gap, resilience_gap, overdue_remediation — each explainable and individually
  evidenced (see `scripts/calculate_or_transform.py`). Unknown-status items are reported as
  `not_evaluable`, never as pass/fail.
- **Controls:** R3; hard boundary against any supplier decision (approve/reject/onboard/
  clear/risk-accept), closure/sign-off, filing/attestation, and GRC/TPRM system-of-record
  write; versioned-config thresholds and a documented, reproducible residual-tier mapping;
  considerations required; `required` human adjudication.
- **Scripts:** `validate_input` (assessment schema, evaluability warnings), findings engine,
  `validate_output` (evidence/citation completeness, deterministic tier tie-out, R3
  prohibited-decision screen, disclaimer, considerations).
- **Evaluations:** trigger/routing, golden Critical case, unknown-controls edge, deterministic
  script checks, no-decision safety + injection, register-write authorization.
- **Handoffs:** downstream to `third-party-risk-assessor`,
  `third-party-ai-due-diligence-assistant`, `cyber-incident-response-coordinator`,
  `vulnerability-prioritization-assistant`, `concentration-risk-monitor`,
  `operational-resilience-scenario-tester`, `operational-resilience-reporter`.

### Pending before release
- Domain SME (third-party cyber risk) + control-owner blind review; fairness review of the
  finding/tier logic.
- Confirm the versioned threshold / residual-tier-mapping config source and its owner.
- Wire read-only MCP integrations (vulnerability/cloud posture, incident/BCP, CMDB, IAM,
  supplier evidence, threat intel, config) at deployment.
