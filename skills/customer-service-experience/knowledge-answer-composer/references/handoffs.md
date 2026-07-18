# Adjacent-Skill Handoffs — knowledge-answer-composer

This skill produces a **source-grounded answer object** and stops. It does not advise,
decide, send, or act. Downstream skills consume the answer via its durable `answer_id`.

## Downstream (this skill hands off to)

| Downstream skill | When to route | Handoff artifact |
| ---------------- | ------------- | ---------------- |
| `next-best-action-assistant` | User wants advice, an offer, a retention/save play, or "what should I do" | `answer_id` + question context |
| `complaint-resolution-assistant` | User asks whether a complaint is justified / should be upheld, or wants a resolution drafted | `answer_id` + case context |
| `customer-interaction-summarizer` | User wants a recap of a specific call/chat/email rather than an answer to a question | interaction reference |
| `vulnerable-customer-support-assistant` | The interaction suggests a vulnerability determination or special-support need | case context |
| `omnichannel-case-orchestrator` (R4) | The answer must actually be **sent**, or a refund/escalation/closure executed (gated action) | `answer_id` |

Coverage, eligibility, fraud/AML, and other **binding line-of-business determinations** are
out of scope here: route them to the relevant R3 decision-support skill with mandatory human
adjudication. This skill only states what approved sources say, with citations.

## Upstream (may call this skill)

`customer-interaction-summarizer` and `omnichannel-case-orchestrator` may request a
source-grounded answer from this skill rather than composing one themselves.

## Duplicate-execution prevention

- This skill **only composes an answer** from approved knowledge; it must not perform the
  advice, determination, delivery, or case action that belongs to the skills above.
- Downstream skills must **not** re-retrieve and re-ground the same knowledge when a valid
  `answer_id` for the same question + `as_of_date` + jurisdiction already exists; they reuse
  it and record it against the case.
