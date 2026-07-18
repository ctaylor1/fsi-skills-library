# Adjacent-Skill Handoffs — due-diligence-questionnaire-responder

Drafting the DDQ/RFP response (this skill) is a **separate control activity** from content
ownership, compliance review, and external delivery — each has different entitlements,
accountability, and downstream reliance. This skill emits a durable `questionnaire_id` and a
drafted response manifest; it does not approve content, clear disclosures, or send anything.

## Downstream (this skill hands off to)

| Downstream skill | When | Handoff artifact |
| ---------------- | ---- | ---------------- |
| `communications-compliance-reviewer` | Answers drafted; required-disclosure, prohibited-claim, and supervision review is needed before external delivery | `questionnaire_id` + drafted response + source index |
| `conflicts-of-interest-reviewer` | A question surfaces a potential conflict (e.g., affiliated brokerage, cross-trading) needing disclosure review | `questionnaire_id` + the flagged question and evidence |

## Upstream (feeds this skill)

| Upstream skill | Provides |
| -------------- | -------- |
| `performance-attribution-builder` | Reconciled performance/attribution figures cited in returns answers |
| `portfolio-exposure-analyzer` | Exposure / positioning figures cited in portfolio answers |
| `fund-fact-sheet-builder` | Controlled fact-sheet figures and disclosures reusable as source data |

The controlled content library and the required-disclosure register produce the approved
answers and disclosures. This skill is **interactive** drafting (`aws-fsi-scheduled-agent:
no`); a monitor may populate an RFP queue but must not draft, approve, or deliver.

## Non-catalog handoffs (human / licensed / operations)

- **Unsupported / stale / data-gap / unapproved-source questions** → routed to the named
  **content owner** (IR, Product, Risk, InfoSec, Finance, Operations, Responsible Investment)
  to author or refresh approved content. No catalog skill authors approved DDQ content; this
  is a human content-owner step.
- **Content and compliance sign-off** → the content owners and the registered principal /
  compliance approve the answers; this skill records approvals but never grants them.
- **External delivery** of the completed response → a human approves and delivers via the
  approval broker; this skill never sends or submits.

## Duplicate-execution prevention

- This skill **does not** author approved content, clear disclosures, decide conflicts, build
  performance, or deliver the response — those belong to the named skills or to a human.
- The compliance reviewer consumes this skill's `questionnaire_id`/manifest rather than
  re-drafting the answers.
- A question with ambiguous or missing approved content is left `unsupported`/`data-gap` for a
  content owner, never auto-answered here.
