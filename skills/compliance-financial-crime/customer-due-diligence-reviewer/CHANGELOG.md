### Independent forward repair — 2026-10-03

- Reject copied receipt monetary provenance before activity aggregation.

# Changelog — kyc-customer-due-diligence-screener

## 0.2.0 — 2026-10-03

- Added source-bound Phase2 cdd-lifecycle/1.0 supplied-evidence workflow, exact detached-output validation, inherited issue/access controls and distinct adjacent-skill boundaries.
- Reviewed current primary sources and added synthetic native fixture/golden/tamper tests and adversarial/unknown regressions.
- No live actions; approval/source authentication/practitioner acceptance not claimed.
- Preserved original Phase1 schema, calculator helpers, public compute/package aliases, fixtures and regression tests; distinct explicit mode selects Phase2.

## [0.1.1] — 2026-09-21

Phase 1 repairs the bounded supplied-evidence implementation. Explicit applicable policy profiles replace silent approved defaults; unknown evidence remains unknown. Native output requires detached original-input reconstruction, rejects unvalidated additions and states source truth as unverified.

This Phase 1 implementation screens supplied onboarding evidence. Periodic/event-driven lifecycle orchestration, independently verified digital identity, expected-activity assessment and legal beneficial-ownership analysis are not implemented. A lifecycle CDD review remains a future extension of this job.

Domain rules, fixtures, handoffs and input/output contracts now match the implementation. Added 24 adversarial regression cases covering policy provenance, source binding and domain failure modes. Source pointers and synthetic fixtures are not independent verification or production acceptance. Human domain/control-owner review and any live integration remain pending. Earlier 0.1.0 claims below are historical and superseded where inconsistent with this entry and current rules.

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
