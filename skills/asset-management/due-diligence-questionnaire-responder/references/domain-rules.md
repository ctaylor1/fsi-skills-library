# Domain Rules — due-diligence-questionnaire-responder

Orientation references: the firm's DDQ/RFP content standard, the controlled content library
(owners, effective dates, expiry, approval status), the required-disclosure register, and the
SEC marketing rule (17 CFR 275.206(4)-1) constraints on performance and claims. These take
precedence and are **versioned contracts**. This skill applies the deterministic drafting
rules below; it does not exercise investment or marketing judgment and provides no advice.

## Response status (deterministic, per question)

For each question, resolve a single candidate answer (explicit `matched_answer_id`, else a
single approved topic match) and assign:

| Status | Condition | Consequence |
| ------ | --------- | ----------- |
| `drafted` | Approved, in-date library/prior answer matches; any required data point is present and in-date | Cited answer text drafted into its response |
| `stale` | Matched approved answer exists but `expires` < `as_of_date` | Cited **and** listed as an open item (refresh) — still flagged as not-current |
| `data-gap` | Answer requires a data point that is missing or stale | Routed to the data owner; **no figure fabricated** |
| `unapproved-source` | Only non-approved content (`draft`/`in-review`/`expired`) matches | Routed to the content owner for approval; **no drafted text** |
| `unsupported` | No approved content matches, or the topic matches **more than one** approved answer (ambiguous) | Routed to the content owner; **no drafted text** |

Precedence: the **approved-source gate is checked before freshness and data** — non-approved
content can never be drafted from, regardless of dates. Only `drafted` and `stale` responses
carry answer text, and both must carry a citation to an approved source.

## Matching and response consistency

- With `matched_answer_id`: use that answer if it exists in the library or prior-answer pool;
  otherwise `unsupported` (id not found).
- Without it: match by `topic`. **Exactly one** approved answer → use it. **More than one**
  approved answer for the topic → `unsupported` (ambiguous; the owner must select one, so the
  response stays internally consistent). **Zero** approved answers → `unsupported` (no source).
- The content library wins over prior answers on an id collision. Prior answers are only used
  when no library entry supplies the topic.

## Stale-language detection

Staleness is determined by `expires` versus `as_of_date` on both content answers (→ `stale`)
and data points (→ `data-gap`). Stale content is drafted-but-flagged so a reviewer can see the
current-looking text alongside its expiry; a stale/missing data point never yields a
fabricated figure.

## Required disclosures

- The input's `required_disclosures` with trigger `always` are always included.
- Whenever any answer cites performance/data (`data_cited`), the **standard performance
  disclosure** is included: "Past performance is not indicative of future results. Figures are
  as of the stated date, may be gross of fees, and are subject to change and to verification by
  the content owner." `validate_output` fails closed if it is absent when data is cited.

## Approvals capture (recorded, never assumed)

- Approvals with `status == "recorded"` are captured with `type`, `approver_role`, `approver`
  (masked), `date`, and `citation`.
- Every entry in `required_approvals` (e.g., `compliance-approval`, `product-approval`) with no
  recorded approval becomes an **outstanding** approval and an open item. Approval is never
  assumed. `human_approval_required_before_delivery` is always `true`.

## Open-items taxonomy

`unsupported-question` | `stale-answer` | `data-gap` | `unapproved-source` |
`outstanding-approval`. Each open item names the item, its type, the routing owner, a required
human action, and (where a source exists) its citation.

## Hard boundaries (fail closed)

- No **fabricated answers** (unsupported/data-gap/unapproved questions carry no drafted text).
- No **unapproved content** used as an answer.
- No **performance/return guarantees** or claims absent from the approved source.
- No **completeness/final overclaim** and no **delivery/submission** (draft-only).
- No **personalized investment, legal, or tax advice**.

## Response manifest — required contents

`config_version`, `questionnaire_id`, `product`, `jurisdiction`, `as_of_date`,
`template_version`, `draft_status: draft-assembled`,
`human_approval_required_before_delivery: true`, `question_count`, the canonical `sections`
(response summary, respondent profile, responses, data appendix, disclosures, approvals, open
items, source index), the open-items list, and the standing note.
