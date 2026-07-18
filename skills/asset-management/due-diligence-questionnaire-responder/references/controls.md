# Controls — due-diligence-questionnaire-responder

- **Risk tier:** R2 — analytical / drafting support. **Action mode:** Draft-only; no
  system-of-record change. The output is a draft response for human review, not a submission,
  a binding commitment, or investment advice.
- **Human approval:** `external-delivery` — content owners and compliance must review and
  approve before any answer is relied on, sent, or submitted to a client, investor, or
  consultant. Internal analytical drafting may be reviewer-sampled.

## Prohibited (fail closed)

- **Fabricating an answer**: authoring content for a question that has no approved,
  in-date library or prior answer. Unsupported questions are routed to a content owner.
- **Using unapproved content**: drafting from `draft` / `in-review` / `expired` content.
  Only `approved` content is used; anything else is an unapproved-source open item.
- **Unsupported / promotional claims**: return or performance guarantees, "will outperform",
  "risk-free", "assured returns", or any claim not present in the approved source.
- **Completeness / final overclaims**: "response is complete", "all questions answered",
  "no open items", "final response", "approved for submission".
- **Delivery / submission**: sending, submitting, filing, transmitting, or delivering the
  response. Draft-only.
- **Personalized investment, legal, or tax advice** to the questionnaire's sender.

## Response states (this skill may set only these)

Per question: `drafted` | `stale` | `unapproved-source` | `data-gap` | `unsupported`.
Response package: `draft-assembled` only. It may **not** set `final`, `submitted`,
`approved`, or `delivered`.

## Required output screens (`scripts/validate_output.py`)

- All required template sections present (mirrors [../assets/output-template.md](../assets/output-template.md)):
  response summary, respondent profile, responses, data appendix, disclosures, approvals,
  open items, source index.
- Every `drafted`/`stale` answer carries a citation **and** `source_approved: true` (no
  unsupported/unapproved claims); every `unsupported`/`data-gap`/`unapproved-source` response
  carries **no** drafted answer text (fabrication guard).
- When any answer cites performance/data, the standard performance disclosure is present.
- Recorded approvals carry `type`, `approver_role`, `date`, and `citation`; missing required
  approvals appear as outstanding open items; `human_approval_required_before_delivery` is
  `true`.
- No delivery/submission, performance-guarantee, or completeness/overclaim language.
- `draft_status` equals `draft-assembled`.
- Standing note present: "Draft DDQ/RFP response for human review only. Every answer is drawn
  from approved content and cited; no answer is fabricated. Content owners and compliance must
  review and approve before any answer is sent or submitted to a client, investor, or
  consultant."

## Segregation of duties

Drafting entitlements are distinct from content ownership, compliance review, and external
delivery. The same person/skill must not both draft the response and approve its content or
release it. Approving content and releasing the response are separate, human-owned controls.

## Data classification, privacy, records

- **Highly Confidential — MNPI / client-confidential.** DDQ content and prospect identity may
  be material and non-public. Mask client/prospect identifiers to what the response requires;
  do not expose non-public holdings or unpublished performance beyond the approved figures.
- Retain the response manifest, citations, and content/config/template versions per the firm's
  marketing-and-RFP recordkeeping policy (including SEC marketing-rule books-and-records where
  applicable); log the drafter identity on every read and draft.
- Keep data within the deployment's residency boundary.
