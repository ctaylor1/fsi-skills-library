# Controls — fee-and-charge-reviewer

- **Risk tier:** R2 — analytical. **Action mode:** Read-only analysis.
- **Human approval:** `external-delivery` — required before any question set or remediation
  request goes to a customer or a case/system of record.

## Prohibited (fail closed)

- No **legal/regulatory-violation determination** — never state or imply a fee is unlawful,
  illegal, non-compliant, or "violates" a law, regulation, or disclosure.
- No **binding refund/adjustment decision** — never decide or promise a refund, credit,
  waiver, adjustment, or reversal ("we will refund", "the bank owes", "entitled to a refund").
- No **fee action** — never reverse, waive, or credit a charge; those are authorized-system
  actions taken by a human after review.
- No **legal advice** — never recommend suing, a lawsuit, or assert a legal claim.
- No **inferred terms** — never guess a disclosed amount, cap, or waiver; use only the
  provided fee schedule and the recorded `config_version`.

## Required output screens (`scripts/validate_output.py`)

- Every flagged finding (any non-`matches_disclosed` status) has ≥ 1 cited evidence row.
- `review_outcome` equals the deterministic mapping from finding statuses (see
  [domain-rules.md](domain-rules.md)).
- No prohibited language (regex screen: `violates`, `unlawful`, `illegal`, `non-compliant`,
  `breach`, `we will refund`, `the bank owes`, `entitled to a refund`, `reverse the fee`,
  `issue a credit`, `has been refunded/reversed/credited/waived`, `file a lawsuit`, etc.).
- Standing disclaimer present: "Fee review and questions only; not a legal conclusion, refund
  decision, or legal advice, and not a reversal or credit of any charge."
- `questions` and a `remediation_request_draft` are included when any finding is flagged.

## Fairness / conduct

- Compare against the disclosed schedule only; do not use protected-class attributes or
  proxies. Describe charges factually; avoid stigmatizing or accusatory language about the
  bank or the customer.

## Data classification, privacy, records

- **Highly Confidential (customer NPI/PII).** Mask account/card numbers to last 4.
- Minimize customer data to what evidences a flagged finding.
- Retain the review + citations + schedule/`config_version` per records policy; log the read
  and any external-delivery approval.

## Reproducibility

`review_id` binds the output to the exact posted fees, disclosed schedule version, statement
period, and `config_version`; re-running with the same inputs reproduces the findings and the
review outcome.
