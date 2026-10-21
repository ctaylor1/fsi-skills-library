<!--
DDQ / RFP Response — output template (ddq-response-template@0.1.0)
Draft & package deliverable. Section headers below mirror the canonical `sections` keys
enforced by scripts/validate_output.py (REQUIRED_SECTIONS). Populate every {{placeholder}}
from the assembled manifest. Every `drafted` / `stale` answer MUST carry its citation and be
drawn from APPROVED content; every `unsupported` / `data-gap` / `unapproved-source` question
is routed to a content owner and carries NO drafted text. This is a DRAFT for human review —
never a final, submitted, or client-ready response.
-->

# DDQ / RFP Response (DRAFT) — {{questionnaire_id}}

> Draft DDQ/RFP response for human review only. Every answer is drawn from approved content
> and cited; no answer is fabricated. Content owners and compliance must review and approve
> before any answer is sent or submitted to a client, investor, or consultant.

## Response Summary
- Questionnaire ID: {{questionnaire_id}}
- Product / strategy: {{product}} / {{strategy}} | Jurisdiction: {{jurisdiction}}
- Client (masked): {{client_masked}} | Client type: {{client_type}}
- As-of date: {{as_of_date}}
- Config / template version: {{config_version}} / {{template_version}}
- Draft status: **draft-assembled**
- Human approval required before delivery: **yes**
- Counts: drafted {{n_drafted}} · stale {{n_stale}} · unapproved-source {{n_unapproved}} · data-gap {{n_data_gap}} · unsupported {{n_unsupported}} · open items {{n_open_items}}

## Respondent Profile
- Product / strategy: {{product}} / {{strategy}}
- Jurisdiction: {{jurisdiction}}
- Client type: {{client_type}} | Client (masked): {{client_masked}}

## Responses
For each question, one response record. Drafted/stale answers show cited text; routed
questions show the reason and the owner they go to (no drafted text):

- **{{question_id}}** [{{section}}] — status: **{{status}}**
  - Answer: {{answer_text_or_ROUTED}}
  - Source: {{answer_id}} — owner: {{owner}} ({{owner_role}}) — effective: {{effective_date}}{{expires_note}}
  - Cite: {{citations}}
  - Note: {{reason_if_any}}

## Data Appendix
Approved, in-date data points cited by the responses:

- {{data_id}} — {{label}}: {{value}} (as of {{as_of}}) — cite: {{citation}}

## Disclosures
Required disclosures for this response (always-on plus any triggered by cited performance/data):

- {{disclosure_id}}: {{disclosure_text}} — source: {{disclosure_source_ref}}

## Approvals
Recorded:
- {{approval_type}} — {{approver_role}} — {{approval_date}} — cite: {{approval_citation}}

Outstanding (required, not yet recorded):
- {{outstanding_approval_type}} — status: outstanding

## Open Items
Every question or item requiring human action before this response can be reviewed and sent:

- [{{open_item_type}}] {{item}} — owner: {{owner}} — action: {{required_action}} {{open_item_citation}}

## Source Index
Deduplicated citations backing every drafted answer, data point, disclosure, and approval:

- {{citation}}

---
Handoff: route the drafted response to `communications-compliance-reviewer` for the required
disclosure / prohibited-claim / supervision review, and route every open item to its named
content owner. This skill drafts from approved content only — the content owners' approval,
the compliance review, and external delivery are separate, human-owned steps.
