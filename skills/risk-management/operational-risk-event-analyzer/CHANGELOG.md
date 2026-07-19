# Changelog — operational-risk-event-analyzer

## [0.1.0] — 2026-07-17
Initial authoring in the FSI Skills Library (baseline status: `new`). R3 decision-support:
analysis, cited evidence, escalation candidates, and remediation recommendations only, with
mandatory human adjudication and no autonomous decision, closure, filing, or system-of-record
write.

- **Scope:** Basel event-type/business-line classification, impact quantification (gross loss,
  recoveries, net loss, indirect costs, banding amount), cause→control-theme→root-cause mapping,
  regulatory-reporting and board-notifiable escalation candidates, deterministic severity band,
  and remediation recommendations. Read-only; no risk decision, escalation, filing, or write.
- **Deterministic engine (`scripts/calculate_or_transform.py`):** documented arithmetic and the
  cause/threshold/severity mappings; each finding carries a cited `source_ref`; the primary
  root cause uses a fixed tie-break for reproducibility.
- **Controls:** R3; hard boundary against risk determination, residual-risk acceptance, event
  closure, regulatory filing, journal posting, and risk-register updates; versioned-config
  thresholds only; mandatory human adjudication.
- **Scripts:** `validate_input` (event schema, taxonomy and evaluability warnings), the analysis
  engine, and `validate_output` (impact tie-out, deterministic severity, escalation
  under-flag screen, evidence/citation completeness, adjudication flag, decision/closure/filing
  language screen, standing disclaimer).
- **Evaluations:** trigger/routing, golden Critical case (with board + reporting candidates),
  near-miss edge, deterministic script checks, no-decision safety fixture + injection, and an
  adjudication-required authorization check.
- **Handoffs:** downstream to `third-party-risk-assessor`, `cyber-incident-response-coordinator`,
  `ai-incident-investigator`, `suspicious-activity-report-drafter`, `complaint-resolution-assistant`,
  `key-risk-indicator-monitor`, `risk-control-self-assessment-assistant`, and
  `operational-resilience-reporter`; ERM adjudication, board escalation, and regulatory filing
  route to a human / authorized system.

### Pending before release
- Domain SME (operational risk) + control-owner blind review; fairness review of cause/theme
  mapping and root-cause language.
- Confirm the versioned threshold/mapping config source and its ERM owner, and the jurisdiction
  packs for operational-risk regulatory-reporting thresholds.
- Wire read-only MCP integrations (loss-event/GRC, finance/GL, incident, change, HR, third-party
  inventory, reference data, config) at deployment.
