# Changelog — merchant-onboarding-risk-reviewer

## [0.1.0] — 2026-07-17
Initial authoring in the FSI Skills Library (baseline status: `new`).

- **Scope:** explainable merchant-onboarding risk findings + cited evidence + a
  deterministic recommendation band and required conditions. Read-only R3 decision-support;
  no onboarding decision, no boarding/decline, no case closure, no filing/system-of-record
  write.
- **Findings (deterministic):** sanctions-screening and prohibited-business-model (blocking);
  restricted-business-model, adverse-media, beneficial-ownership-gap, high-risk-geography,
  pep-ownership, expected-activity-outsized, credit-exposure, website-product-risk
  (elevated); evidence-incomplete (incomplete). Each explainable and evidenced (see
  `scripts/calculate_or_transform.py`).
- **Recommendation mapping:** blocking → Recommend-Decline; incomplete →
  Escalate-Insufficient-Evidence; elevated → Recommend-Approve-with-Conditions; none →
  Recommend-Approve. Documented in `references/domain-rules.md`.
- **Controls:** R3; `required` human adjudication; hard boundary against onboarding
  decisions, sanctions/adverse-media adjudication, case closure, and filing/system writes;
  versioned-config lists/thresholds only; standing disclaimer required; `adjudication_required`
  forced true.
- **Scripts:** `validate_input` (application schema, evaluability warnings), finding engine,
  `validate_output` (fired tie-out, evidence/citation completeness, deterministic
  recommendation tie-out, prohibited-decision/closure/filing screen, disclaimer, conditions
  and adjudication checks).
- **Evaluations:** trigger/routing, golden Approve-with-Conditions case, insufficient-evidence
  and blocking-decline edges, deterministic script checks, no-decision safety (non-compliant
  fixture fails closed) + injection, human-adjudication authorization.
- **Handoffs:** specialist screens `sanctions-match-adjudicator`, `adverse-media-investigator`,
  `beneficial-ownership-verifier`, `kyc-customer-due-diligence-screener`,
  `enhanced-due-diligence-packager`, `credit-memo-drafter`; downstream
  `payment-fraud-case-investigator`, `real-time-payment-risk-monitor`,
  `stablecoin-payment-controls-reviewer`, `dispute-operations-assistant`.

### Pending before release
- Domain SME (merchant risk / payments risk) + control-owner blind review; fairness review
  of findings and geography/PEP handling.
- Confirm the versioned prohibited/restricted MCC lists, high-risk geographies, and
  thresholds source and its owner.
- Wire read-only MCP integrations (KYB/registry, sanctions & adverse-media screening,
  application intake, website review, fraud/credit, config) at deployment.
