# Changelog — customer-risk-rating-reviewer

## [0.1.1] — 2026-09-21

Phase 1 repairs the bounded supplied-evidence implementation. Explicit applicable policy profiles replace silent approved defaults; unknown evidence remains unknown. Native output requires detached original-input reconstruction, rejects unvalidated additions and states source truth as unverified.

This is arithmetic reproduction and evidence challenge, not methodology validation, independent factor classification, legal prohibition determination, override authorization or customer lifecycle orchestration. All factor definitions and institutional policy applicability are supplied assertions.

Domain rules, fixtures, handoffs and input/output contracts now match the implementation. Added 24 adversarial regression cases covering policy provenance, source binding and domain failure modes. Source pointers and synthetic fixtures are not independent verification or production acceptance. Human domain/control-owner review and any live integration remain pending. Earlier 0.1.0 claims below are historical and superseded where inconsistent with this entry and current rules.

## [0.1.0] — 2026-07-17
Initial authoring in the FSI Skills Library (baseline status: `new`).

- **Scope:** deterministic recomputation of a customer's KYC/AML risk rating from the approved
  weighted-factor methodology, a challenge against the rating of record, and cited findings +
  a recommended review outcome. Read-only; R3 decision support with mandatory human adjudication.
- **Recomputation (deterministic):** weighted-factor score → band mapping with mandatory PEP
  (High) and sanctions-nexus (Prohibited) floors; explainable, reproducible, never tuned to the
  individual (see `scripts/calculate_or_transform.py`).
- **Findings:** rating_discrepancy, mandatory_floor, expired_override, undocumented_override,
  unassessed_trigger, stale_factor, missing_required_factor — each cited to a source row or the
  methodology contract.
- **Outcome mapping (deterministic precedence):** Escalate-For-Adjudication > Remediate-Data-First
  > Re-Rate-Recommended > Align-No-Change.
- **Controls:** R3; hard boundary against setting/changing a rating, approving/validating an
  override, disposing of a trigger, closing a review, or filing; versioned methodology only;
  `adjudication_required` always true; `required` human approval.
- **Scripts:** `validate_input` (case schema, data-quality/evaluability warnings), recomputation
  engine, `validate_output` (finding/citation completeness, deterministic band + outcome tie-out,
  discrepancy-must-be-flagged, decision/closure/filing language screen, disclaimer, routing).
- **Evaluations:** trigger/routing, golden Escalate-For-Adjudication case, missing-required-factor
  edge, deterministic script checks, no-decision safety + injection, human-adjudication authorization.
- **Handoffs:** upstream from `kyc-customer-due-diligence-screener`, `aml-alert-triager`,
  `regulatory-exam-response-packager`; downstream to `enhanced-due-diligence-packager`,
  `sanctions-match-adjudicator`, `adverse-media-investigator`,
  `transaction-monitoring-alert-investigator`, `beneficial-ownership-verifier`,
  `suspicious-activity-report-drafter`.

### Pending before release
- Domain SME (financial-crime program) + control-owner blind review; fairness review of factors.
- Confirm the versioned CRR methodology config source, its owner, and the mandatory-floor policy.
- Wire read-only MCP integrations (KYC/AML case, screening, monitoring, adverse-media, config)
  at deployment.
