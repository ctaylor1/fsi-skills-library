# Adjacent-Skill Handoffs — agent-permission-scope-reviewer

This skill produces a cited **scope-review pack** (`review_id`) and stops. It does not
adjudicate, accept risk, grant/revoke entitlements, or clear an agent for production.

## Downstream (route the human/adjudicator to)

| Downstream skill / system | When | Handoff artifact |
| ------------------------- | ---- | ---------------- |
| IAM / entitlement adjudication (human + system) | The scope must be approved, conditioned, or rejected and entitlements granted/revoked | `review_id` + findings |
| GRC risk-acceptance / waiver workflow | A finding will be accepted as residual risk or waived (human-filed) | `review_id` + finding evidence |
| `prompt-and-agent-risk-reviewer` | The concern is prompt/instruction/memory/retrieval/guardrail content, not tool scope | agent id + prompts/tools |
| `ai-evaluation-benchmark-builder` | The agent needs a trigger/safety/regression evaluation suite built | agent id + task spec |
| Model inventory / model-risk-documentation | The need is registry inventory or SR 11-7 style model documentation | model id |

## Upstream (may call this skill)

AI-system intake, change-management, and skill-onboarding workflows may request a scope
review before an access grant. A scheduled monitor is **not** used here (this skill is
interactive, `aws-fsi-scheduled-agent: no`).

## Duplicate-execution prevention

- This skill evaluates the manifest and evidences **findings only**; it must not reach an
  access decision, grant/revoke/provision an entitlement, close the review, or file a
  waiver — those belong to the human adjudicator and the downstream systems.
- Downstream adjudication reuses the `review_id` evidence rather than re-deriving findings;
  the `policy_version` on the pack makes the review reproducible and auditable.
