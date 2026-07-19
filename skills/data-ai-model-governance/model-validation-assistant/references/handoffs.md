# Adjacent-Skill Handoffs — model-validation-assistant

This skill performs **independent validation** and **drafts validation findings** for
adjudication. It does not maintain the model inventory, assemble the governed model documentation
pack, assess enterprise/model risk, analyze the impact of a model change, investigate a live
incident, or make the validation decision. Those are separate control activities with distinct
entitlements — and validation independence from development must be preserved.

## Upstream (feeds this skill)

| Upstream source / skill | Provides | Handoff artifact |
| ----------------------- | -------- | ---------------- |
| `model-inventory-maintainer` / model registry | The model of record, its tier, owner, version, and declared controls | `model_id` + `model_tier` + control list |
| `ai-evaluation-benchmark-builder` / evaluation harness | Independent performance, benchmark, robustness, and back-testing evidence | `evalharness:*` run refs |
| Model risk framework / template library | Required areas, materiality mapping, approver routing, validation-report template | `framework_version` |

## Adjacent — do NOT use this skill for (route instead)

| If the request is… | Route to |
| ------------------ | -------- |
| Maintaining the model inventory / registry record | `model-inventory-maintainer` |
| Assembling / finalizing the governed model documentation pack (validation report of record) | `model-risk-documenter` |
| Building the AI/model risk assessment (likelihood x impact, control coverage) | `ai-risk-assessment-builder` |
| Building or refreshing an evaluation benchmark suite | `ai-evaluation-benchmark-builder` |
| Analyzing the impact of a proposed model change / re-validation trigger | `model-change-impact-analyzer` |
| Investigating a data-quality issue found during validation | `data-quality-issue-investigator` |
| Documenting data lineage | `data-lineage-documenter` |
| Investigating a live model/AI incident | `ai-incident-investigator` |

## Downstream (human, not a skill)

The reviewed findings are adjudicated by the **model validation lead and the routed approver**
(Head of Model Validation / Model Risk Committee + CRO per the overall severity). Separately, the
adjudicated validation report of record is assembled and maintained by `model-risk-documenter`.
This skill emits a `validation_id`-keyed draft with `validation_outcome.status: pending` and
`adjudication_required: true`; it must not approve, certify, clear the model, close a finding,
file, or assemble the documentation pack.

## Duplicate-execution prevention

- This skill **does not** maintain the inventory, assemble documentation, decide, or close —
  those belong to the routes above or to a human.
- A pack carries `validation_id` and `framework_version` so a reviewer works one authored draft
  rather than re-validating; `model-risk-documenter` consumes the adjudicated findings rather
  than re-deriving them.
- A `needs-data` pack or an open finding is resolved by a human (obtain independent evidence /
  remediate / adjudicate), never force-completed or auto-closed here.
