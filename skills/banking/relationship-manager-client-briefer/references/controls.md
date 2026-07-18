# Controls — relationship-manager-client-briefer

- **Risk tier:** R2 — analytical / drafting support. **Action mode:** Draft-only; no
  system-of-record change. The skill assembles a source-cited brief for human review; it
  makes no writes and stages nothing for execution.
- **Human approval:** `external-delivery` — a human must review and authorize before the
  brief is delivered (to the client, committee, or file) or any CRM / system of record is
  changed. Internal drafting may be reviewer-sampled. When the brief informs a credit action,
  renewal, or covenant matter, credit/risk review is required (recorded in the approvals
  block).

## Prohibited (fail closed)

- **Delivering / sending / submitting / filing** the brief, or **writing the CRM** or any
  system of record (logging calls, notes, opportunities, contacts, actions).
- **Credit, covenant, pricing, or risk-rating decisions** — approving/declining/renewing a
  facility, waiving/curing a covenant breach, committing to a rate or spread, or changing a
  customer risk rating. Breaches and at-risk covenants are **surfaced**, not adjudicated.
- **Personalized investment, financial, tax, or legal advice** to the client or the RM.
- **Fabricating** any exposure, covenant status, profitability figure, news item, contact,
  opportunity, or action to fill the brief. Unsourced content is stripped.
- **Guessing client identity** or a contact when the entity is unresolved.
- **Adjudicating adverse media / financial crime** — adverse news is routed to a specialist.

## Statuses (this skill may set only these)

`needs-data` | `unresolved-entity` | `unsupported-content` | `stale-source` | `draft-brief`
(packageable). It may **not** set any state implying delivery, approval, or a system write.

## Required output screens (`scripts/validate_output.py`)

- **Template fidelity:** required sections present; no unfilled `{{placeholder}}` tokens.
- **No unsupported claims:** packageable record is entity-resolved and fully source-cited
  (`content_integrity.all_sourced`), free of blocking critical stale sources; every listed
  content item and exposure line carries a citation.
- **Exposure tie-out:** `total_committed` / `total_outstanding` equal the sum of the lines.
- **Required approvals recorded:** `reviewer_signoff_required = true` and a non-empty
  `approvals.required` block are present.
- **No delivery/CRM-write language;** **no credit/covenant/pricing/risk-rating decision or
  commitment language;** **no investment/legal/tax advice language.**
- **Standing note present.** Fail closed on any miss.

## Segregation of duties

Brief drafting is distinct from credit adjudication, covenant waiver, pricing, risk-rating,
and delivery. The same person/skill must not both draft the brief and authorize the credit or
covenant decision it may inform.

## Data classification, privacy, records

- **Highly Confidential (customer NPI/PII).** Apply data minimization — include only the
  relationship context the brief needs; do not pull unrelated customer data into a brief.
- Respect each source's classification; do not elevate restricted content into a
  wider-distribution pack.
- Retain the draft brief, the `as_of_date`, template version, and source citations with the
  client record; log every read and every brief produced with the preparer identity.
  Delivery and any CRM write are human actions outside this skill.
