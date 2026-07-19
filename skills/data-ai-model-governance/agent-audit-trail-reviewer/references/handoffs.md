# Adjacent-Skill Handoffs — agent-audit-trail-reviewer

This skill produces a cited **agent-run findings pack** (`review_id`) and stops. It does not
adjudicate, attest, close, file, or investigate to disposition.

## Downstream (route the human/reviewer to)

| Downstream skill | When | Handoff artifact |
| ---------------- | ---- | ---------------- |
| `ai-incident-investigator` | A finding indicates a harmful, unauthorized, biased, privacy, or security event needing evidence preservation and remediation coordination | `review_id` + implicated events |
| `agent-permission-scope-reviewer` | An out-of-scope-tool finding needs a full tool-by-tool least-privilege / entitlement map | `review_id` + tool_call events |
| `prompt-and-agent-risk-reviewer` | Findings point to prompt, guardrail, memory, or injection weaknesses in the agent's design (not just the trail) | `review_id` + prompt/override events |
| `model-change-impact-analyzer` | The trail implicates an undocumented model/agent change requiring scope and revalidation analysis | `review_id` + run header |
| `model-inventory-maintainer` | The agent/model is missing or mis-registered in the inventory | `review_id` + agent/model identifiers |
| `data-quality-issue-investigator` | The concern is a data defect (uncited/incorrect retrieved source), not an agent-control gap | `review_id` + retrieval events |

## Upstream (may call this skill)

`ai-incident-investigator` and `model-validation-assistant` may request an audit-trail review
as evidence for a case or validation. A scheduled monitor is **not** used here (this skill is
interactive, `aws-fsi-scheduled-agent: no`).

## Human / operations hand-off (no catalog skill)

Adjudication of findings, control attestation, and **logging/closing an issue in the risk or
issue register** are performed by the **internal-audit lead, control owner, or AI/model-risk
governance function** and their authorized systems — never by this skill. The pack is
evidence for that human decision.

## Duplicate-execution prevention

- This skill computes and evidences **findings only**; it must not attest, decide, close,
  file, or write a system of record — those belong to the human adjudicator and, where
  applicable, the downstream skills above.
- Downstream skills reuse the `review_id` evidence rather than re-deriving the findings.
