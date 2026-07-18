# Adjacent-Skill Handoffs — ai-evaluation-benchmark-builder

Designing the benchmark (this skill) is a **separate control activity** from running it,
analyzing results, and approving a model — different entitlements, artifacts, and decisions.
This skill emits a `spec_version`-keyed **draft benchmark package** with
`governance_approval: pending`; it must not run, score, decide, or approve.

## Upstream (feeds this skill)

| Upstream skill | Provides | Handoff artifact |
| -------------- | -------- | ---------------- |
| `ai-use-case-intake-classifier` | Governance path + provisional risk tier that route a use case to evaluation | model_id + risk rating + required review set |
| `model-inventory-maintainer` | The authoritative inventory record, materiality tier, ownership | `model_id` + registry ref + materiality |

## Downstream (this skill hands off to)

| Downstream skill | When | Handoff artifact |
| ---------------- | ---- | ---------------- |
| Authorized evaluation harness (engineering / MLOps, human-operated — no catalog skill) | Governance has approved the benchmark; the evaluations are executed against the model | approved benchmark package (thresholds/datasets/samples) |
| `model-validation-assistant` | After a run, results are analyzed against the approved thresholds and baselines as validation outcome evidence | run results + approved acceptance rules |
| `model-risk-documenter` | MRM assembles the independent validation / model-risk documentation pack | approved benchmark + results |

## Specialist test design (route out; do not do here)

| Specialist skill | When |
| ---------------- | ---- |
| `prompt-and-agent-risk-reviewer` | Deep adversarial/jailbreak and prompt-injection probe review beyond naming the safety dataset |
| `ai-risk-assessment-builder` | Disparate-impact / fairness assessment across protected populations |
| `agent-permission-scope-reviewer` | Least-privilege review of the agent's tool scope (not an evaluation) |

## Duplicate-execution prevention

- This skill **does not** execute evaluations, compute results, analyze outcomes, or make a
  release decision — those belong downstream.
- Governance approval is a **human** gate; the benchmark is never self-approved and never
  routed to execution until an approver signs off.
- A `needs-data` / `needs-calibration` evaluation is resolved by a human supplying the
  dataset or the approved threshold — never by inventing a number here.
