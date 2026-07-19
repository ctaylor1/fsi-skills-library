# Changelog — kyc-customer-due-diligence-screener

## [0.1.0] — 2026-07-17
Initial authoring in the FSI Skills Library (baseline status: `new`).

- **Scope:** explainable CDD signals + cited evidence + a deterministic recommended review
  track. Read-only (R3 decision support); no CDD decision, no rating, no disposition, no
  closure, no filing.
- **Signals (deterministic):** completeness (`missing_required_field`,
  `missing_required_document`, `expired_document`), identity (`unverified_identity`,
  `identity_mismatch`), risk factors (`high_risk_jurisdiction`, `high_risk_industry`,
  `pep_flag`, `sanctions_potential_match`, `adverse_media_flag`), and beneficial ownership
  (`ownership_over_100`, `ubo_below_coverage`, `ubo_unverified`) — each explainable and
  evidenced (see `scripts/calculate_or_transform.py`).
- **Track mapping:** Escalate-For-Adjudication > EDD-Recommended > Remediate-First >
  Standard-CDD, deterministic and shared verbatim with `validate_output`.
- **Controls:** R3; hard boundary against any CDD decision, sanctions/PEP disposition,
  risk-rating write, case closure, or filing; versioned-config thresholds/lists only;
  mandatory human adjudication (`aws-fsi-human-approval: required`); tipping-off / SAR
  confidentiality.
- **Scripts:** `validate_input` (case schema, evaluability warnings), signal engine,
  `validate_output` (evidence/citation completeness, deterministic track tie-out,
  `adjudication_required` check, prohibited decision/closure/filing/disposition screen,
  standing disclaimer, routing next-steps).
- **Evaluations:** trigger/routing, golden EDD-Recommended case, individual thin-data edge,
  deterministic script checks, no-decision safety fail-closed fixture + injection,
  human-adjudication authorization.
- **Handoffs:** upstream `customer-onboarding-document-checker`; downstream
  `sanctions-match-adjudicator`, `enhanced-due-diligence-packager`,
  `beneficial-ownership-verifier`, `adverse-media-investigator`,
  `customer-risk-rating-reviewer`, `transaction-monitoring-alert-investigator`,
  `suspicious-activity-report-drafter`.

### Pending before release
- Domain SME (financial-crime / FIU) + control-owner blind review; fairness review of the
  higher-risk lists and signals.
- Confirm the versioned config source (required fields/documents, thresholds, higher-risk
  country/industry lists) and its owner.
- Wire read-only MCP integrations (KYC/AML case, sanctions/PEP, adverse-media, registry,
  transaction monitoring, config) at deployment.
