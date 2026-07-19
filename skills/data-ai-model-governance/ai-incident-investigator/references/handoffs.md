# Adjacent-Skill Handoffs — ai-incident-investigator

Detection/triage, **investigation** (this skill), remediation ownership, and
adjudication/closure are **separate control activities** with different entitlements,
evidence depth, and case states. This skill investigates a reported incident and emits a
durable `case_id` + cited evidence bundle; it routes remediation but performs none of it.

## Upstream (feeds this skill)

The risk/issue system (and, for security-flavored signals, `security-alert-triage-assistant`)
produces the reported incident. Detection and first-line enrichment are **not** part of this
skill. This skill is **interactive** (`aws-fsi-scheduled-agent: no`); a read-only monitor may
*populate* an incident record but must not investigate, determine, or close.

## Downstream (this skill routes remediation to — recommendations only)

| Downstream skill | When | Handoff artifact |
| ---------------- | ---- | ---------------- |
| `model-change-impact-analyzer` | Remediation may require a model/agent change | `case_id` + evidence bundle |
| `model-validation-assistant` | Independent revalidation of the implicated model | `case_id` + behavioral evidence |
| `model-risk-documenter` | Model documentation / validation-evidence pack must be updated | `case_id` + findings context |
| `ai-risk-assessment-builder` | Fairness/AI-risk reassessment after a `biased` incident | `case_id` + impact estimate |
| `prompt-and-agent-risk-reviewer` | Hypothesis points to prompt/agent design or prompt injection | `case_id` + agent trail |
| `agent-permission-scope-reviewer` | `unauthorized` action / over-broad tool scope | `case_id` + tool-call evidence |
| `data-quality-issue-investigator` | Hypothesis points to a data defect | `case_id` + affected datasets |
| `data-lineage-documenter` | Affected-data lineage must be traced | `case_id` + dataset refs |
| `data-loss-prevention-incident-assistant` | `privacy` exposure / potential exfiltration | `case_id` + exposure evidence |
| `cyber-incident-response-coordinator` | `security` event needing formal IR + containment | `case_id` + chronology |
| `operational-resilience-reporter` | `resilience`/availability event with impact-tolerance/reporting implications | `case_id` + impact estimate |
| `operational-risk-event-analyzer` | Every incident — log the operational-risk (loss/near-miss) event | `case_id` + impact estimate |
| `agent-audit-trail-reviewer` | Preserve/replay the agent trail for reproducibility | `case_id` + trace refs |
| `third-party-ai-due-diligence-assistant` | Hypothesis points to a third-party model/data dependency | `case_id` + dependency refs |

## Human handoffs (no skill — route in prose)

- **AI governance / model risk committee** — adjudicates the disposition and owns closure,
  root-cause determination, and any model exoneration or redeployment authorization.
- **Legal / compliance and the Data Protection Officer** — own any regulatory or breach
  notification decision. This skill never drafts, sends, or files a notification.

## Duplicate-execution prevention

- This skill **does not** determine root cause, close incidents, revalidate models, review
  permissions, or file notifications — those belong downstream or to human owners.
- Downstream skills consume the `case_id`/bundle rather than re-investigating.
- Related prior incidents are **linked** for human review, never auto-merged or auto-closed.
