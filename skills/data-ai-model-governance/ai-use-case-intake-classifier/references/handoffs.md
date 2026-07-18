# Adjacent-Skill Handoffs — ai-use-case-intake-classifier

This skill produces a cited **intake classification record** (`classification_id`): fired risk
factors, a governance tier, a recommended governance path, and the specific required reviews. It then
**stops**. It does not perform the substantive reviews, assess the use case in depth, register it, or
reach a governance decision.

## Downstream (route the human/reviewer to)

| Downstream skill | When | Handoff artifact |
| ---------------- | ---- | ---------------- |
| `ai-risk-assessment-builder` | Tier High/Limited needs the full data/model/fairness/privacy/security/oversight assessment | `classification_id` + fired factors |
| `model-inventory-maintainer` | The use case/model must be registered (ownership, lineage, purpose) | `classification_id` + use-case attributes |
| `prompt-and-agent-risk-reviewer` | `genai_or_agentic` fired — prompts/tools/memory/retrieval/guardrails need review | `classification_id` + model type |
| `agent-permission-scope-reviewer` | `autonomous_action` fired — least-privilege tool/permission mapping | `classification_id` + autonomy |
| `third-party-ai-due-diligence-assistant` | `third_party_model` fired — external provider diligence | `classification_id` + provider |
| `ai-evaluation-benchmark-builder` | Evaluation gate required — task/trigger/regression/safety benchmarks | `classification_id` + purpose |
| `model-validation-assistant` / `model-risk-documenter` | Independent validation / evidence pack required | `classification_id` + tier |

## Upstream (may call this skill)

Governance intake queues and product-onboarding workflows may request a classification for each new
AI proposal. A scheduled monitor is **not** used here (this skill is interactive,
`aws-fsi-scheduled-agent: no`).

## Duplicate-execution prevention

- This skill classifies and routes **only**; it must not build the risk assessment, review prompts,
  register the model, or reach a governance decision — those belong to the human governance body and
  the downstream skills.
- Downstream skills reuse the `classification_id` and its fired factors rather than re-deriving the
  tier, so the intake is classified once and reviewed consistently.
