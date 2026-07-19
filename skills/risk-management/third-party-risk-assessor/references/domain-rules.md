# Domain Rules — third-party-risk-assessor

Deterministic scoring of the eight third-party risk **dimensions** and how they map to a
**suggested composite risk tier**. Thresholds are configuration (versioned, owned by the
Enterprise Risk Management / third-party-risk team), not hard-coded judgments, and are never
tuned to an individual vendor. Orientation references: the firm's third-party / outsourcing
risk-management standard and applicable supervisory guidance (e.g., US interagency
third-party risk guidance) take precedence over this file; align the config to them.

## Severity ladder

Each dimension resolves to one band: **Low (0)**, **Moderate (1)**, **High (2)**,
**Critical (3)**. A dimension with severity ≥ 2 is a **material finding** and must carry
cited evidence in the output.

## Dimension rules (default config)

| Dimension | Critical (3) | High (2) | Moderate (1) | Evidence attached |
| --------- | ------------ | -------- | ------------ | ----------------- |
| `criticality` | Supports a critical operation AND substitutability ≥ `critical_substitution_days` (30) | Supports a critical operation, OR substitutability ≥ `high_substitution_days` (14), OR annual spend ≥ `material_spend` (1,000,000) | Spend ≥ `moderate_spend` (250,000) OR substitutability ≥ 7d | Criticality profile row |
| `control_evidence` | Any control gap in a `critical_control_domains` domain (encryption/access/resilience) | ≥ `high_gap_count` (3) control gaps (status partial/ineffective/missing OR stale > `control_test_max_days`) | 1 to `high_gap_count` − 1 such gaps, none in a critical domain | The gapped control rows (material findings only) |
| `concentration` | Single point of failure AND share ≥ `critical_share` (0.75) | Share ≥ `high_share` (0.5) OR single point of failure | Share ≥ `moderate_share` (0.25) | Concentration row |
| `subcontractors` | Any critical subcontractor in an `elevated_risk_jurisdictions` country | Any critical subcontractor OR any undisclosed subcontractor | Any subcontractor present | The flagged fourth-party rows |
| `data` | Classification `restricted`, OR PII with records ≥ `critical_records` (100,000) | Classification `confidential`, OR PII present | Classification `internal` | Data-handling row |
| `resilience` | Supports a critical operation AND (BCP not tested OR RTO > `max_rto_hours` 24) | BCP not tested, OR last test stale > `bcp_test_max_days`, OR RTO > `high_rto_hours` (8) | SLA uptime < `sla_min` (0.999) | Resilience row |
| `financial_condition` | Going-concern flag, OR credit rating in `distressed_ratings` (CCC–D), OR current ratio < `critical_current_ratio` (1.0) | Net margin < 0, OR debt/equity > `high_debt_to_equity` (3.0), OR rating in `speculative_ratings` (BB/B) | Current ratio < `moderate_current_ratio` (1.5) | Financial-statement row |
| `exit_contingency` | Supports a critical operation AND exit plan not documented | Exit plan not documented, OR no alternate provider identified | Documented but not tested | Exit-plan row |

Dimensions are independent; each is reported with its own band, reason, and evidence. There
is no opaque composite score — the composite tier is a documented function of the bands.

## Composite suggested tier (deterministic)

Let `mx` = the highest dimension severity and `n_high` = the count of dimensions at High or
above (severity ≥ 2).

| Suggested tier | Rule |
| -------------- | ---- |
| **Critical** | `mx == 3` (any Critical dimension), OR `mx == 2` and `n_high ≥ high_dimension_count` (default 3) |
| **High** | `mx == 2` and `n_high < high_dimension_count` |
| **Moderate** | `mx == 1` |
| **Low** | `mx == 0` or no evaluable dimensions |

`high_dimension_count` is a **versioned config threshold** (default 3), not a hard-coded
constant: both the scoring engine and the output validator read it from the pack config, so a
tightened deployment value (e.g., escalate at 2 High dimensions) escalates consistently and
the fail-closed tie-out screen honors the same value.

The suggested tier is a **triage/prioritization recommendation for the accountable
third-party-risk committee**. It is not an approval, a rejection, a risk-acceptance, or an
onboarding/renewal/termination decision, and it never triggers an action.

## Not-evaluable handling

A dimension whose required input block is absent is reported under `not_evaluable` /
`evidence_gaps` and is **excluded** from the composite (it does not silently default to Low).
The output states which dimensions could not be evaluated so the reviewer can obtain the
missing evidence.

## Hard boundaries (fail closed)

- Never **approve, reject, onboard, renew, terminate, offboard, or risk-accept** a vendor, or
  state that any of these has been decided — those are human/committee decisions.
- Never **close, file, or attest** the assessment, or write it to a system of record.
- Never tune thresholds to the individual vendor or infer "what is acceptable for this
  vendor" outside the versioned config.
- Financial-condition scoring is a **factual solvency/creditworthiness read for risk
  assessment**; it is not investment advice and must not recommend buying/holding/selling any
  security or the vendor's debt.
- Describe control, data, and jurisdiction facts **factually**; do not assert misconduct or
  intent.

## Considerations the reviewer must weigh (always surface when material findings exist)

Compensating controls not captured in the input, a remediation plan already underway,
contractual protections (indemnities, audit rights, step-in rights), recent independent
assurance (SOC 2 Type II, ISO 27001), the business owner's tolerance for the function, and
whether the assessment inputs are current. The pack must invite the committee to weigh these
against the findings.
