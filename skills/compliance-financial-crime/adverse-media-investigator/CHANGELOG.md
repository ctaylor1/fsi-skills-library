# Changelog — adverse-media-investigator

## [0.1.0] — 2026-07-17
Initial authoring in the FSI Skills Library (baseline status: `new`). Created as the
casework skill that turns adverse-media / negative-news hits into a durable case with a cited
evidence bundle and a disposition **recommendation**, distinct from the regulated decisions it
feeds (sanctions adjudication, risk-rating change, EDD sign-off, SAR filing).

- **Scope:** entity resolution (subject vs. namesake), source-quality tiering,
  allegation-vs-finding-vs-resolved classification, documented materiality scoring, durable
  `case_id` + evidence bundle (chronology, parties, amounts, citations). Read-only; every
  disposition is a *recommendation* for a human adjudicator.
- **Controls:** R3; no case closure/clearance/determination/filing; no attribution on a name
  match alone (unresolved subjects → `needs-data`); sanctions/PEP proximity routes out; no
  risk-rating recalculation; SAR-confidentiality / tipping-off screen; versioned scoring
  config.
- **Scripts:** `validate_input` (screening-batch schema, needs-data + tier/recency warnings),
  investigation engine (entity resolution + source/assertion classification + materiality +
  disposition + evidence bundle), `validate_output` (durable case_id, recommendation-only
  dispositions, band/score tie-out, citation coverage, closure/determination/filing +
  tipping-off screen, standing note).
- **Evaluations:** trigger/routing, golden 5-subject batch exercising every disposition
  (escalate-EDD, monitor, route-sanctions-pep, needs-data, no-material-adverse-media),
  deterministic script checks, fail-closed safety on a non-compliant fixture, name-attribution
  refusal, tipping-off refusal, determination/closure authorization refusal.
- **Handoffs:** downstream to `enhanced-due-diligence-packager`, `sanctions-match-adjudicator`,
  `customer-risk-rating-reviewer`, `due-diligence-packager`, and (post-investigation)
  `suspicious-activity-report-drafter`; upstream from `kyc-customer-due-diligence-screener`,
  `beneficial-ownership-verifier`, `aml-alert-triager`, `transaction-monitoring-alert-investigator`,
  `merchant-onboarding-risk-reviewer`, `customer-onboarding-document-checker`.

### Pending before release
- FIU/AML control-owner + legal (SAR-confidentiality) blind review; segregation-of-duty review.
- Confirm the scoring config (source tiers, category weights, materiality bands) source, owner,
  and versioning; localize category/jurisdiction packs beyond the US default.
- Wire read-only MCP integrations (case-mgmt, KYC/CDD, sanctions/PEP flags, regulatory/court
  corpus, adverse-media retrieval, records archive) at deployment.
