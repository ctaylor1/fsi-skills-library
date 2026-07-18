# Adjacent-Skill Handoffs — customer-interaction-summarizer

This skill produces a **normalized interaction summary** and stops. It does not advise,
decide, or act. Downstream skills consume the summary via its durable `summary_id`.

## Downstream (this skill hands off to)

| Downstream skill | When to route | Handoff artifact |
| ---------------- | ------------- | ---------------- |
| `next-best-action-assistant` | User wants the next step, an offer, a save/retention play, or advice | `summary_id` + interaction context |
| `complaint-resolution-assistant` | User asks whether a complaint is justified or wants a resolution drafted | `summary_id` + complaint reference |
| `call-quality-compliance-reviewer` | User asks whether the interaction met QA / compliance | `summary_id` + transcript reference |
| `vulnerable-customer-support-assistant` | User asks whether the customer is vulnerable or needs special support | `summary_id` + interaction context |
| `service-recovery-assistant` | User wants a goodwill / service-recovery gesture decided or drafted | `summary_id` |
| `knowledge-answer-composer` | User wants the customer's question answered from approved knowledge | interaction context (no decision) |
| `omnichannel-case-orchestrator` (R4) | Any gated action — send, refund, escalate, close the case | `summary_id` + case reference |

## Upstream (may call this skill)

`next-best-action-assistant`, `complaint-resolution-assistant`,
`call-quality-compliance-reviewer`, `vulnerable-customer-support-assistant`, and
`service-recovery-assistant` may request a fresh summary from this skill rather than
re-reading and re-normalizing the transcript themselves.

## Duplicate-execution prevention

- This skill **only summarizes**; it must not perform next-best-action, complaint,
  compliance, vulnerability, service-recovery, or case-action work — those belong to the
  skills above.
- Downstream skills must **not** re-summarize a transcript when a valid `summary_id` for the
  same `interaction_id` already exists; they reuse it.
