# Adjacent-Skill Handoffs — beneficial-ownership-verifier

This skill produces a cited **UBO verification pack** (`verification_id`) and stops. It does
not screen owners, assemble the EDD package, rate risk, adjudicate, close, or file.

## Downstream (route the human/analyst to)

| Downstream skill | When | Handoff artifact |
| ---------------- | ---- | ---------------- |
| `kyc-customer-due-diligence-screener` | First-line CDD screening of the entity and each identified UBO (completeness, identity, sanctions/PEP, escalation need) | `verification_id` + identified UBOs |
| `sanctions-match-adjudicator` | An identified owner produces a potential sanctions/PEP match needing adjudication | owner identity + ownership context |
| `adverse-media-investigator` | Adverse-media assessment on an identified owner | owner identity |
| `enhanced-due-diligence-packager` | Escalated / higher-risk entity needs an EDD package (source of funds/wealth, geography, ownership evidence) | `verification_id` + ownership evidence + gaps |
| `customer-risk-rating-reviewer` | Ownership/control findings should feed a risk-rating (re)calculation | `verification_id` + UBO set |
| `customer-onboarding-document-checker` | Missing/expired ownership documents need remediation before human approval | gap list (missing/expired documents) |
| `suspicious-activity-report-drafter` | The adjudicator decides an obscured-ownership pattern may warrant a SAR (draft-only, human-filed) | `verification_id` + evidence |

## Upstream (may call this skill)

Legal-entity onboarding case orchestration and `kyc-customer-due-diligence-screener` may
request a UBO verification pack. No scheduled monitor is used here (this skill is
interactive, `aws-fsi-scheduled-agent: no`).

## Duplicate-execution prevention

- This skill computes and evidences **ownership + control and the reconciliation gaps only**;
  it must not screen owners against sanctions/PEP, assemble the EDD package, rate risk, reach
  an onboarding disposition, close the case, or file — those belong to the human adjudicator
  and the downstream skills.
- Downstream skills reuse the `verification_id` pack and its citations rather than
  recomputing the ownership graph.
