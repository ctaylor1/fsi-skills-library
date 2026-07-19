# Adjacent-Skill Handoffs — regulatory-exam-response-packager

This skill **assembles** a response package from evidence other skills and humans produce. It
does not perform the underlying analysis, and it does not submit anything.

## Upstream (feeds this skill — evidence and status to package)

| Upstream skill | Contributes | Handoff artifact |
| -------------- | ----------- | ---------------- |
| `aml-alert-triager` | Alert-queue posture and escalation counts | Triage records + `case_id`s |
| `transaction-monitoring-alert-investigator` | Investigated case evidence for TM-related requests | Case evidence bundle |
| `sanctions-match-adjudicator` | Sanctions/PEP screening evidence | Adjudication records |
| `suspicious-activity-report-drafter` | SAR program evidence (aggregate; confidentiality-controlled) | Approved, human-filed SAR references |
| `kyc-customer-due-diligence-screener` | CDD/KYC control evidence | Screening results |
| `enhanced-due-diligence-packager` | EDD packages for high-risk relationships | EDD package refs |
| `customer-risk-rating-reviewer` | Risk-rating methodology/output evidence | Rating review records |
| `policy-procedure-gap-analyzer` | Issue / gap status for finding responses | Gap findings |
| `regulatory-change-impact-analyzer` | Applicability of rules cited in requests | Impact analysis |
| `audit-evidence-packager` | Independent-audit evidence packages | Audit evidence refs |
| `regulatory-reporting-data-validator` | Data-quality evidence for reporting-related requests | Validation results |
| `risk-control-self-assessment-assistant` | Control status for control-adequacy requests | RCSA output |

Cite each contributed artifact by its source reference; do not re-derive or re-adjudicate it.

## Downstream (human, not a skill)

There is **no** skill that submits an exam response. Submission to the regulator, closure of an
exam item, and any regulated attestation are **human actions** owned by **regulatory affairs /
compliance / legal**. This skill hands the reviewed draft package to that owner; the owner (not
the agent) submits it and updates the exam system of record.

## Duplicate-execution prevention

- This skill **does not** investigate, adjudicate, rate, or file — those belong to the upstream
  skills and to authorized humans.
- It consumes upstream `case_id`s / evidence references rather than reproducing the analysis.
- It never marks an item ready without the required human approvals, and never submits or
  closes — so it cannot duplicate or pre-empt the human submission step.
