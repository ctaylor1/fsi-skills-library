# Adjacent-Skill Handoffs — third-party-ai-due-diligence-assistant

This skill is **third-party AI due-diligence drafting** for external providers, models, and
data. It assembles evidence and a recommended disposition for a human to adjudicate; it does
not classify the use case, build evaluations, review agent permissions, decide onboarding, or
maintain the inventory. Those are separate control activities with distinct entitlements.

## Upstream (feeds this skill)

| Upstream source / skill | Provides | Handoff artifact |
| ----------------------- | -------- | ---------------- |
| `ai-use-case-intake-classifier` | The classified use case, governance tier, and third-party-exposure flag that scopes the assessment | governance tier + intake record |
| AI governance policy / due-diligence rubric | Required domains per criticality, evidence types, freshness windows, risk-flag rubric, hard gates | `rubric_version` |
| Provider evidence room / model registry / data catalog | The due-diligence artifacts and the registered model/data records | evidence items + registry/catalog refs |

## Adjacent — do NOT use this skill for (route instead)

| If the request is… | Route to |
| ------------------ | -------- |
| Classifying the AI/agent **use case** or assigning a governance tier | `ai-use-case-intake-classifier` |
| **Building** an evaluation benchmark or eval harness (rather than consuming its results) | `ai-evaluation-benchmark-builder` |
| Reviewing an external **agent's tool-and-operation permission scope** for least privilege | `agent-permission-scope-reviewer` |
| Reviewing **prompt/agent design risk** (jailbreak, injection, unsafe tool use) | `prompt-and-agent-risk-reviewer` |
| Creating or updating the **model/agent inventory record** after a decision | `model-inventory-maintainer` |

## Downstream (human, then a skill)

The reviewed package is **adjudicated by an authorized human** (third-party risk committee /
accountable AI-governance owner), who makes the onboarding decision. Only after that decision
does `model-inventory-maintainer` record the outcome. This skill emits an `engagement_id`-keyed
draft package with `residual_risk_rating`, a `recommended_disposition`, and
`human_adjudication_required: true`; it must not make or record the decision.

## Duplicate-execution prevention

- This skill **does not** classify use cases, build evaluations, review permission scope, or
  update inventory — those belong to the routes above or to a human.
- A package carries the `engagement_id` and `rubric_version` so a reviewer adjudicates one
  authored draft rather than re-assessing.
- A blocked record (`insufficient-evidence`, `stale-evidence`, `unsupported-finding`,
  `needs-data`) is resolved by a human (obtain evidence / refresh / classify), never
  force-packaged.
