# Adjacent-Skill Handoffs — service-recovery-assistant

Service recovery (this skill) drafts a remediation + communication package for a **service
failure** and stops at a human approval gate. It is distinct from formal complaint
handling, from vulnerability assessment, and from the execution of the outcome.

## Upstream (feeds this skill)

| Upstream skill | Provides |
| -------------- | -------- |
| `customer-interaction-summarizer` | The interaction summary, commitments, and sentiment that establish what happened |
| `knowledge-answer-composer` | Approved policy / product-term answers used to ground the explanation |

## Downstream / referral (this skill routes to)

| Skill / destination | When | Handoff artifact |
| ------------------- | ---- | ---------------- |
| `complaint-resolution-assistant` | The matter is a **formal / regulated complaint** needing a final-response decision (out of scope here) | `case_id` + failure summary |
| `vulnerable-customer-support-assistant` | A **vulnerability** flag is present; accommodations / specialist support are needed | `case_id` + vulnerability context (Tier 3 approval also forced) |
| `next-best-action-assistant` | The customer needs a broader policy-compliant next action beyond this recovery | `case_id` + customer context |
| `omnichannel-case-orchestrator` | **After approval**, the approved package must be delivered and any adjustment coordinated across channels/systems | approved package + `case_id` |
| `call-quality-compliance-reviewer` | The interaction itself needs a quality/conduct review | interaction reference |

## Human / operations handoffs (no catalog skill)

- **Approval of the goodwill/redress spend and the external delivery** is a human authority
  at the computed tier (agent / team lead / operations manager). This skill records the
  required approval; it does not grant it.
- **Payment or system-of-record posting** of goodwill/redress is performed by authorized
  operations under the approval broker, never by this skill.

## Duplicate-execution prevention

- This skill **does not** decide a formal complaint, assess vulnerability accommodations,
  send communications, or pay/post remediation — those belong to the skills/roles above.
- The approved package carries a durable `case_id`; downstream delivery consumes it rather
  than re-drafting.
- A `refer-specialist` disposition hands the case off intact; the recovery is not drafted
  in parallel.
