# Controls — client-review-preparer

- **Risk tier:** R3 — regulated/control decision support. **Action mode:** Draft-only; no
  system-of-record change. The pack is evidence + discussion points for a licensed human.
- **Human approval:** `required` — mandatory human adjudication before the pack is used in a
  client meeting, before any recommendation is made, and before any delivery or CRM write.
  Internal drafting may be reviewer-sampled.

## Prohibited (fail closed)

- **Investment recommendation**, **suitability determination**, or **trade** of any kind
  (the pack surfaces sourced discussion points; recommendations route to
  `suitability-reg-bi-reviewer` and a licensed human).
- **Case closure**, **filing**, or **CRM / system-of-record write**.
- **Send / submit / deliver** of the pack (drafting only — delivery is a separate human step).
- **Personalized investment, legal, or tax advice.**
- Any statement a **cited source** does not support; guessing client/account **identity**.

## Assembly statuses (this skill may set only these)

`needs-data` | `unresolved-entity` | `account-identity-gap` | `unsupported-content` |
`stale-source` | `tieout-break` | `disclosure-gap` | `draft-review`. It may **not** set
`final`, `approved`, `recommended`, `filed`, `delivered`, or `closed`.

## Required output screens (`scripts/validate_output.py`)

- Template fidelity: required sections present; no unfilled `{{placeholder}}` tokens.
- No unsupported claims: packageable record is entity-resolved and fully cited; every content
  item and every holding carries a citation; citations non-empty.
- Client & account identity: only `draft-review` is packageable; accounts carry
  `account_id`/`type`/`registration` and a citation.
- Performance & holdings tie-out: per-account and household roll-up tie out; any
  `household_reported_value` matches.
- Disclosure coverage: `disclosure_check.missing` is empty.
- Required approvals recorded: `reviewer_signoff_required=true` and a non-empty `approvals`
  block.
- No recommendation/suitability/trade language; no decision/closure/filing/CRM-write language;
  no send/submit/deliver language; no investment/legal/tax advice.
- Standing note present.

Fail closed on any miss; a defective or overreaching pack cannot be presented as ready-to-use.

## Segregation of duties

Preparation is distinct from recommendation, suitability review, supervision, and any trade
or delivery. The same person/skill must not both prepare the pack and adjudicate the
recommendation or authorize a trade.

## Data classification, privacy, records

- **Highly Confidential (customer NPI/PII).** Include only the relationship context the review
  needs (data minimization); do not pull unrelated customer data into a pack, and do not
  elevate restricted content into a wider-distribution deck.
- Retain the draft pack, the `as_of_date`, config/template version, and source citations with
  the client record; log every read and every pack produced with the preparer identity.
  Delivery and any CRM write are human actions outside this skill.
