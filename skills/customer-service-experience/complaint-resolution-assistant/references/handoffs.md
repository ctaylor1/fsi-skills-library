# Adjacent-Skill Handoffs — complaint-resolution-assistant

Drafting a complaint resolution is a **separate control activity** from deciding it,
delivering it, and reporting it. This skill produces a review-ready draft; humans and other
skills own the decision, the customer contact, the payment, and any regulatory return.

## Upstream (feeds this skill)

| Upstream skill | Provides | Handoff artifact |
| -------------- | -------- | ---------------- |
| `customer-interaction-summarizer` | Summarized calls/chats/emails, commitments, disclosures | Interaction summary + links, used to build the chronology |
| `knowledge-answer-composer` | Source-linked answer on applicable policy/product terms | Cited standards to assess the complaint against |

## Downstream / lateral (this skill routes to)

| Skill | When | Handoff artifact |
| ----- | ---- | ---------------- |
| `omnichannel-case-orchestrator` | Approved response must be delivered, or redress paid / account changed (execution) | `complaint_id` + approved draft package (requires human approval) |
| `vulnerable-customer-support-assistant` | A vulnerability indicator is present | `complaint_id` + flag evidence (accommodation review before finalizing) |
| `service-recovery-assistant` | It is a service failure / goodwill gesture without a logged, regulated complaint | Interaction context (not a complaint package) |
| `call-quality-compliance-reviewer` | Root cause points to an agent-conduct or disclosure failure needing QA review | `complaint_id` + interaction reference |

## Human / specialist handoffs (no catalog skill)

- **Decision authority** — the uphold/reject determination and any ex-gratia/redress sign-off
  is made by the complaints handler / conduct-risk approver, not this skill.
- **Regulatory complaints reporting** — periodic complaints returns and root-cause reporting
  to a regulator are handled by the complaints / compliance team; this skill only flags that
  a report may be required.
- **Legal / ombudsman referral** — threatened litigation, or a customer's escalation to an
  external ombudsman, routes to legal / the licensed specialist.

## Duplicate-execution prevention

- This skill **does not** decide, send, pay, close, or file — those belong to the human owner
  or, for execution, to `omnichannel-case-orchestrator` under approval.
- Downstream consumers act on the emitted `complaint_id` package rather than re-drafting.
- A `refer-specialist` route is resolved by the named owner, not auto-actioned here.
