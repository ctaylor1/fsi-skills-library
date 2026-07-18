# Adjacent-Skill Handoffs — vulnerable-customer-support-assistant

This skill produces a cited **support-needs assessment** (`assessment_id`): the customer's
observed signals, the possible support-need drivers, approved-catalog accommodation suggestions,
and a suggested referral route. It stops at a draft that a human reviews; an authorized colleague
records any marker, applies any accommodation, and makes any referral. It never diagnoses,
determines capacity, limits service, advises, writes to a system of record, or contacts the
customer.

## Upstream (feeds this skill)

| Upstream skill / actor | Why it routes here | Handoff artifact |
| ---------------------- | ------------------ | ---------------- |
| `customer-interaction-summarizer` | A summarized call/chat surfaces signals worth supporting | interaction summary + transcript refs |
| `omnichannel-case-orchestrator` | A case spanning channels needs a support-needs draft attached | case id + interaction record |
| `complaint-resolution-assistant` | A complaint reveals a possible support need alongside the grievance | complaint text + customer_ref |

## Downstream (route the human/colleague to)

| Downstream skill / actor | When | Handoff artifact |
| ------------------------ | ---- | ---------------- |
| **Vulnerability specialist / safeguarding team (human, not a skill)** | A specialist or safeguarding referral is suggested; abuse or risk of harm is disclosed | `assessment_id` (human-delivered) |
| **Financial-difficulty / collections support team (human, not a skill)** | A resilience/arrears signal warrants forbearance support | `assessment_id` + resilience signals |
| `next-best-action-assistant` | After human review, an approved accommodation is turned into a customer-facing offer | approved accommodation codes |
| `service-recovery-assistant` | The interaction also needs service recovery after a poor experience | case id + accommodation context |
| `call-quality-compliance-reviewer` | QA review of how the vulnerability was handled | `assessment_id` + interaction |

## Do not conflate

| Adjacent skill | Difference |
| -------------- | ---------- |
| `customer-interaction-summarizer` | Neutral summary of an interaction — not a support-needs assessment |
| `complaint-resolution-assistant` | Resolves a complaint — this skill drafts support-needs suggestions, not resolutions |
| `next-best-action-assistant` | Selects the next approved action/offer — it consumes this draft after review, it does not replace the review gate |

## Duplicate-execution prevention

- This skill computes the **signal map, accommodation suggestions, and suggested referral
  only**; it must not record a marker, apply an accommodation, make a referral, diagnose, or
  advise — those belong to an authorized human, a specialist/safeguarding team, or a licensed
  professional.
- Downstream actors reuse the `assessment_id` work-product rather than re-deriving it; nothing is
  recorded or sent without human approval.
