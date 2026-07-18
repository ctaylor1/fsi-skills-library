# Adjacent-Skill Handoffs — ai-risk-assessment-builder

This skill **drafts** an AI risk assessment pack for adjudication. It does not classify use
cases, independently validate models, review agent behavior, perform vendor diligence, or
make the risk decision. Those are separate control activities with distinct entitlements.

## Upstream (feeds this skill)

| Upstream source / skill | Provides | Handoff artifact |
| ----------------------- | -------- | ---------------- |
| `ai-use-case-intake-classifier` | Use-case metadata and the **inherent risk tier** | `intake_ref` + `inherent_risk_tier` |
| Model registry | The model/system of record, owner, version, declared controls | `model_ref` + control list |
| `ai-evaluation-benchmark-builder` / `model-validation-assistant` / evaluation harness | Fairness, performance, robustness evidence | `evalharness:*` run refs |
| Control framework / template library | Required domains, matrix, approver routing, template | `framework_version` |

## Adjacent — do NOT use this skill for (route instead)

| If the request is… | Route to |
| ------------------ | -------- |
| Classifying / intaking a use case or setting its inherent tier | `ai-use-case-intake-classifier` |
| Independent model validation, benchmarking, or challenger testing | `model-validation-assistant`, `ai-evaluation-benchmark-builder` |
| Prompt / agent behavioral risk review; agent permission scoping | `prompt-and-agent-risk-reviewer`, `agent-permission-scope-reviewer` |
| Third-party AI vendor due diligence | `third-party-ai-due-diligence-assistant` |
| Data lineage / data-quality investigation | `data-lineage-documenter`, `data-quality-issue-investigator` |
| Investigating a live AI incident | `ai-incident-investigator` |
| Maintaining the model inventory record | `model-inventory-maintainer` |

## Downstream (human, not a skill)

The reviewed pack is adjudicated by the **accountable risk owner and the routed approver**
(AI Risk Officer / Model Risk Committee per the overall rating). This skill emits an
`assessment_id`-keyed draft with `approval.status: pending` and `adjudication_required: true`;
it must not approve, certify, accept risk, or clear the system.

## Duplicate-execution prevention

- This skill **does not** validate, classify, review agents, or decide — those belong to the
  routes above or to a human.
- A pack carries `assessment_id` and `framework_version` so a reviewer works one authored
  draft rather than re-scoring.
- A `needs-data` pack or an open finding is resolved by a human (obtain evidence / remediate
  / adjudicate), never force-completed or auto-closed here.
