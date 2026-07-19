# Adjacent-Skill Handoffs — model-change-impact-analyzer

This skill produces a cited **change-impact pack** (`assessment_id`) and stops. It does not
perform revalidation, update records, or adjudicate/deploy the change.

## Downstream (route the human/adjudicator to)

| Downstream skill | When | Handoff artifact |
| ---------------- | ---- | ---------------- |
| `model-validation-assistant` | The recommendation calls for independent revalidation of affected components | `assessment_id` + fired dimensions + evidence |
| `ai-evaluation-benchmark-builder` | New/expanded evaluations are needed for the changed behavior or data | `assessment_id` + testing findings |
| `model-risk-documenter` | Assemble the controlled change/validation-evidence documentation pack | `assessment_id` + findings |
| `model-inventory-maintainer` | After a **human** decision, update the inventory version/lifecycle/approval status | decision + `assessment_id` |
| `ai-risk-assessment-builder` | A scope/regulatory change warrants a refreshed AI risk assessment | `assessment_id` + regulatory finding |
| `data-lineage-documenter` / `data-quality-issue-investigator` | A data-source change needs lineage documentation or a data-quality investigation | data finding + source refs |
| `prompt-and-agent-risk-reviewer` / `agent-permission-scope-reviewer` | The change is to an agent's prompt/tools/guardrails/permissions | `assessment_id` + tools/controls findings |

## Upstream (may route into this skill)

- `ai-use-case-intake-classifier` — if intake finds the request is a change to an existing
  model rather than a net-new use case, it routes here.
- `regulatory-change-impact-analyzer` — if a mapped regulatory change drives a model change,
  it routes the model-change delta here.

## Human / operations handoffs (no catalog skill)

- **Independent model validation function** performs the revalidation this skill recommends.
- **Change-governance forum / MRM adjudicator** makes the approve/deploy/waive decision.
- **Model owner** records the human adjudication decision and rationale in the change record.
These are human-gated actions; this skill never performs them.

## Duplicate-execution prevention

- This skill computes and evidences **findings and a recommendation only**; it must not
  revalidate, document, update inventory, adjudicate, or deploy — those belong to the human
  and the downstream skills.
- Downstream skills reuse the `assessment_id` evidence rather than recomputing the delta.
