# Adjacent-Skill Handoffs — model-risk-documenter

This skill **assembles and traces** a model documentation / validation-evidence pack for
adjudication. It does not test or independently validate the model, maintain the inventory
record, assess proposed changes, build the AI risk assessment, or make the approval /
attestation decision. Those are separate control activities with distinct entitlements.

## Upstream (feeds this skill)

| Upstream source / skill | Provides | Handoff artifact |
| ----------------------- | -------- | ---------------- |
| `model-inventory-maintainer` | Model identity, **tier/materiality**, owner, version, lifecycle status | `model_id` + `model_tier` |
| `model-validation-assistant` | Independent validation results, performance/outcomes, limitations, and **validation findings** | `validation:*` refs + open findings |
| `ai-evaluation-benchmark-builder` | Evaluation / benchmark evidence for the performance section | `evalharness:*` run refs |
| `data-lineage-documenter` | Data lineage and provenance for the data / traceability sections | `lineage:*` refs |
| Model-risk framework / documentation template | Required sections, coverage, approver routing, disclaimer | `template_version` |

## Adjacent — do NOT use this skill for (route instead)

| If the request is… | Route to |
| ------------------ | -------- |
| Independent model validation, testing, or challenger analysis | `model-validation-assistant` |
| Building / updating the model inventory record, tier, or lifecycle | `model-inventory-maintainer` |
| Assessing a proposed change and revalidation need | `model-change-impact-analyzer` |
| Building the AI/model **risk assessment** (inherent vs residual scoring) | `ai-risk-assessment-builder` |
| Documenting end-to-end data lineage / investigating data quality | `data-lineage-documenter`, `data-quality-issue-investigator` |
| Prompt / agent behavioral risk review; agent permission scoping | `prompt-and-agent-risk-reviewer`, `agent-permission-scope-reviewer` |
| Third-party AI vendor due diligence | `third-party-ai-due-diligence-assistant` |
| Investigating a live AI incident | `ai-incident-investigator` |

## Downstream (human, not a skill)

The reviewed pack is adjudicated by the **model owner, independent validation, and the routed
approver** (Model Risk Management / Model Risk Committee per the model tier). This skill emits a
`model_id`-keyed draft with `attestation.status: pending` and `adjudication_required: true`; it
must not validate, approve, attest, certify, or clear the model. Filing the completed pack and
recording the approval are authorized-human actions in the governance system, performed **after**
review — not by this skill.

## Duplicate-execution prevention

- This skill **does not** validate, maintain the inventory, score risk, or decide — those belong
  to the routes above or to a human.
- A pack carries `model_id`, `template_version`, and `framework_version` so a reviewer works one
  authored draft rather than re-assembling.
- A `needs-data`/`gap` section or an open finding is resolved by a human (obtain and version the
  evidence, remediate, adjudicate), never force-completed or auto-closed here.
