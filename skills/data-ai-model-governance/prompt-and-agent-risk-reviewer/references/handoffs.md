# Adjacent-Skill Handoffs — prompt-and-agent-risk-reviewer

This skill produces a cited **agent risk-review pack** (`review_id`) with findings, a
recommended rating, and a recommended disposition, then stops. It does not approve, accept
risk, attest, file, or close — those are human adjudications and downstream skills.

## Downstream (route the human/reviewer to)

| Downstream skill | When | Handoff artifact |
| ---------------- | ---- | ---------------- |
| `ai-risk-assessment-builder` | The findings must become the formal AI risk assessment / model-risk register entry | `review_id` + findings |
| `agent-permission-scope-reviewer` | A deep, standalone least-privilege review of tool entitlements/OAuth scopes is needed | `review_id` + tool inventory |
| `ai-evaluation-benchmark-builder` | The C-EVAL-01 gap needs an actual evaluation/benchmark suite designed | `review_id` + agent purpose |
| `agent-audit-trail-reviewer` | The question is about what a deployed agent actually did (runtime logs), not design-time risk | `agent_id` + period |
| `ai-incident-investigator` | An AI incident already occurred and needs investigation | `agent_id` + incident ref |
| `model-change-impact-analyzer` | The agent spec materially changed and the impact must be assessed | `agent_id` + change |

## Upstream (may call this skill)

`ai-use-case-intake-classifier` classifies whether a use case is in scope and routes
qualifying agent/prompt configurations here for design-time risk review. A scheduled monitor
is **not** used (this skill is interactive, `aws-fsi-scheduled-agent: no`).

## Duplicate-execution prevention

- This skill reviews the **design-time configuration** and evidences **findings + a
  recommendation** only; it must not build the formal assessment, adjudicate the tool
  scope in depth, design the eval suite, review runtime logs, or investigate an incident —
  those belong to the human adjudicator and the downstream skills.
- Downstream skills reuse the `review_id` findings rather than recomputing them.
- The deployment decision (approve / accept risk / require remediation) is made by the
  accountable AI risk owner, never by this skill.
