# Controls — coverage-meeting-preparer

- **Risk tier:** R2 — analytical / drafting support. Source-grounded assembly of a deliverable;
  no binding decision. **Action mode:** Draft-only; no system-of-record change.
- **Human approval:** `external-delivery` — a human must review and authorize before the brief
  is delivered or any system of record (CRM, data room) is changed. Where MNPI is present,
  control-room clearance is required before the draft is relied on. Internal drafting may be
  reviewer-sampled.

## Prohibited (fail closed)

- **Sending / distributing / filing / posting / executing** anything — the brief, an email, a
  CRM update, a calendar action. This skill drafts only; a human delivers.
- **Investment recommendation, price target, valuation opinion, or rating**, and any
  personalized **investment, legal, or tax advice** or "you should buy/sell/refinance/sign"
  language. The brief reports sourced facts and frames the counterparty's objectives as
  hypotheses to test — it never opines on value or tells anyone what to do.
- **Unsupported / fabricated content** — any development, figure, quote, issue, or objective
  not backed by a cited, approved, in-inventory source.
- **MNPI in a shareable field / externalization** — private-side material must stay
  internal-only; mixing it into an externally-shareable brief, or externalizing without
  recorded control-room clearance, is an information-barrier breach.
- **Auto-merging** an ambiguous client identity, or presenting stale context as current.

## Brief statuses (this skill may set only these)

`draft-brief` (packageable) | `needs-data` | `unsupported-claims` | `stale-source` |
`barrier-hold`. It may **not** set `sent`, `distributed`, `delivered`, `filed`, `approved`
(as a decision), or `recommended`.

## Required output screens (`scripts/validate_output.py`)

- **Template fidelity:** required sections present and no unfilled `{{placeholder}}` tokens.
- A `packageable` record is **fully source-cited** (content-integrity `all_supported`), free of
  **blocking stale sources**, with a non-empty citations list, a handling label, and
  `reviewer_signoff_required: true`; only `draft-brief` is packageable.
- Every claim carries a non-empty citation whose source **system is on the approved list**; a
  dangling or unapproved citation is an unsupported assertion.
- Every **MNPI claim is internal-only**; if any MNPI is present, `control_room_clearance` is
  recorded as `approved`.
- **Approvals recorded:** `supervisory_review` is `approved`; an `external_delivery_approval`
  slot is present but **never** `sent`/`delivered`/`distributed` (this skill never delivers).
- No send/distribute/file/execute language (regex): `brief/pack/deck sent|distributed|
  delivered|shared`, `I have sent|filed|submitted`, `sent to the client`, `posted to the crm`,
  `filed with`, etc.
- No advice/recommendation language (regex): `we recommend the client buy/sell`, `you should
  buy/sell/sign`, `price target of`, `fair value is/of`, `guaranteed return`, `strong buy`,
  `investment/legal/tax advice`, `our valuation opinion`.
- Standing note present (the draft-only / no-send / no-recommendation / MNPI disclaimer).

## Segregation of duties

Drafting the brief is distinct from supervisory review, control-room clearance, and delivery.
The same person/skill must not both draft and self-approve external delivery; MNPI clearance is
a control-room decision, not a preparer decision.

## Data classification, privacy, records

- **Highly Confidential (MNPI / client-confidential).** Information-barrier discipline applies;
  private-side material is internal-only.
- Data minimization: include only the context needed to prepare for the meeting; mask personal
  identifiers to what the brief requires.
- Retain the DRAFT brief, the `as_of_date`, source citations, the config/template versions, and
  the approvals with the engagement record; log every read and every brief produced with the
  preparer identity. Delivery and any system-of-record change are human actions outside this
  skill.
