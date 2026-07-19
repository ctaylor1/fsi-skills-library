# Adjacent-Skill Handoffs — third-party-risk-assessor

This skill produces a cited **third-party risk assessment pack** (`assessment_id`) with
per-dimension findings, evidence, a suggested composite tier, and remediation
recommendations — then stops. It does not adjudicate, decide vendor status, file, or act.
Every downstream route is a recommendation for a human to initiate.

## Downstream (route the human/reviewer to)

| Downstream skill | When | Handoff artifact |
| ---------------- | ---- | ---------------- |
| `third-party-cyber-risk-reviewer` | A control-evidence or data finding needs deep security/cyber control testing | `assessment_id` + gapped controls |
| `enhanced-due-diligence-packager` | Elevated financial-crime / ownership / jurisdiction exposure warrants EDD on the vendor or its owners | `assessment_id` + data/subcontractor findings |
| `operational-resilience-scenario-tester` | A critical-vendor resilience or exit finding needs scenario/severe-but-plausible testing | `assessment_id` + resilience/exit findings |
| `concentration-risk-monitor` | Vendor/function concentration or a single point of failure should be tracked on an ongoing basis | vendor + function + share |
| `operational-risk-event-analyzer` | A live loss event or incident is linked to the vendor | `assessment_id` + event refs |
| `financial-spreading-assistant` | The financial-condition dimension needs the vendor's statements spread and analyzed | vendor financials |
| `contract-obligation-extractor` | Exit, SLA, audit-right, or termination obligations must be pulled from the vendor contract | contract reference |
| `third-party-ai-due-diligence-assistant` | The vendor supplies AI/model services requiring model-governance due diligence | `assessment_id` + service description |
| `enterprise-risk-assessment-builder` | The assessment feeds the enterprise/entity-level risk assessment | `assessment_id` + suggested tier |

If no catalog skill fits (e.g., the accountable committee's **onboarding/renewal/termination
adjudication and sign-off**, contract negotiation, or booking the decision in the vendor
register), route to the **human third-party-risk committee, procurement, and legal/vendor
management** — those are human and operations actions this skill never performs.

## Upstream (may call this skill)

`procurement-sourcing-assistant` (during sourcing/onboarding due diligence),
`enterprise-risk-assessment-builder`, and `risk-control-self-assessment-assistant` may
request an assessment pack. A scheduled monitor is **not** used here (this skill is
interactive, `aws-fsi-scheduled-agent: no`); ongoing monitoring belongs to
`concentration-risk-monitor` and `key-risk-indicator-monitor`.

## Duplicate-execution prevention

- This skill scores and **evidences dimensions and a suggested tier only**; it must not reach
  a vendor decision, close/file the assessment, or take/recommend a binding action — those
  belong to the human/committee and the downstream skills.
- Downstream skills reuse the `assessment_id` evidence rather than recomputing dimensions;
  monitoring skills own the ongoing surveillance so this interactive assessment is not
  re-run on a schedule.
