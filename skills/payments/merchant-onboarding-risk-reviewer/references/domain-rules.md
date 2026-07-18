# Domain Rules — merchant-onboarding-risk-reviewer

Explainable merchant-onboarding **risk findings** and how the fired set maps to a
**recommendation band** for a human adjudicator. Lists and thresholds are configuration
(versioned, owned by the merchant-risk / payments-risk policy team), not hard-coded
judgments, and are never tuned to an individual applicant. Card-network rules (Visa/
Mastercard acquirer risk programs), BSA/AML program requirements, and the firm's merchant-
risk standard take precedence over any default in this file.

## Finding taxonomy

Each finding is independent, explainable, and attaches its own cited evidence. There is no
opaque composite "approval score".

| Finding | Severity | Fires when (default config) | Evidence attached |
| ------- | -------- | --------------------------- | ----------------- |
| `sanctions_screening` | **blocking** | Sanctions screening status is not `cleared` (i.e., `hit` or `pending`) for entity or any owner | Screening status + `source_ref` |
| `prohibited_business_model` | **blocking** | MCC on the prohibited list (e.g., unlicensed gambling, shell) | MCC + business model + rule ref |
| `restricted_business_model` | elevated | MCC on the restricted list (approvable only with conditions) | MCC + business model + rule ref |
| `adverse_media` | elevated | Adverse-media status `unresolved` (financial-crime/fraud/consumer categories) | Categories + `source_ref` |
| `beneficial_ownership_gap` | elevated | Verified ownership coverage < required %, OR a >= threshold-% owner unverified | Owner rows + verification status |
| `high_risk_geography` | elevated | Merchant or any owner jurisdiction on the high-risk list | Jurisdiction + scope |
| `pep_ownership` | elevated | Any politically exposed beneficial owner present | Owner row + ownership % |
| `expected_activity_outsized` | elevated | Expected monthly volume above the no-EDD threshold | Volume + avg ticket |
| `credit_exposure` | elevated | Requested processing limit above review limit AND credit assessment not `pass` | Limit + assessment |
| `website_product_risk` | elevated | Website or website-review evidence missing (products/claims unconfirmable) | Website + review ref |
| `evidence_incomplete` | incomplete | Any required evidence item missing (KYB, UBO, website review, expected activity, financials) | Missing item list |

Thresholds/lists are configuration: `prohibited_mccs`, `restricted_mccs`,
`high_risk_countries`, `required_ubo_coverage_pct` (default 75), `ubo_threshold_pct`
(default 25), `max_monthly_volume_no_edd` (default 1,000,000), `credit_review_limit`
(default 250,000).

## Recommendation mapping (deterministic, documented)

Evaluated in order; the first matching rule wins:

| Recommendation band | Rule |
| ------------------- | ---- |
| **Recommend-Decline** | Any **blocking** finding fired (`sanctions_screening` or `prohibited_business_model`) |
| **Escalate-Insufficient-Evidence** | No blocking finding, but `evidence_incomplete` fired |
| **Recommend-Approve-with-Conditions** | No blocking / no incomplete, but >= 1 **elevated** finding fired; each fired elevated finding contributes a condition |
| **Recommend-Approve** | No findings fired |

The recommendation is a **recommendation for a human adjudicator**. It is not an onboarding
decision, and it never approves, declines, boards, files, or closes anything. `validate_output`
re-derives this mapping and fails closed on any mismatch.

## Hard boundaries (fail closed)

- Never state or imply that the merchant **has been** approved, declined, boarded, onboarded,
  or rejected — describe risk factually and attribute the decision to the human adjudicator.
- Never **adjudicate** a sanctions or adverse-media hit — consume the screening status and
  route open items to `sanctions-match-adjudicator` / `adverse-media-investigator`.
- Never **close** the case or **file/submit** anything (SAR, network submission, boarding
  write).
- Never tune thresholds/lists to the individual applicant; use only the versioned config.
- `high_risk_geography` and `pep_ownership` describe risk requiring EDD, not intent or guilt.

## Conditions guidance (Recommend-Approve-with-Conditions)

Each fired elevated finding maps to a concrete pre-boarding condition (reserve / delivery-
timeframe review for restricted MCC; adverse-media adjudication; UBO completion; EDD for
high-risk geography; PEP/EDD sign-off; expected-activity substantiation and limits; credit
sign-off; website/product confirmation). Conditions are for the adjudicator to impose and
verify; the skill lists them, it does not enforce or sign them off.
