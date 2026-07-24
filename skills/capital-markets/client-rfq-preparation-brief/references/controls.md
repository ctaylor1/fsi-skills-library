# Controls — client-rfq-preparation-brief

- **Risk tier:** R3 — regulated/control decision support. **Action mode:** Draft-only; no
  system-of-record change.
- **Human approval:** `required` — for any price/quote, firm bid/offer, commitment, execution, or
  suitability determination.

## Prohibited (fail closed)
- No **price, quote, firm bid/offer**; no **committing or executing** for the firm.
- No **suitability/eligibility determination** — flags are surfaced, not adjudicated.
- No **assuming eligibility** for missing client context.

## Required output screen (`scripts/validate_output.py`)
- Every flag and completeness gap carries a citation.
- No pricing/commitment language (regex: we quote/the price is/firm bid/firm offer/we commit/
  executed the trade/filled at/price it at/we can do it at).
- Suggested disposition is review-only (`ready-for-review` | `review-required`).
- Standing disclaimer present.

## Segregation of duties
The brief preparer is not the pricing/suitability authority; the brief supports, never replaces,
the sales trader and compliance.

## Data classification, privacy, records
- **Highly Confidential (customer NPI/PII).** Mask client identifiers to last 4.
- Retain brief + citations; log read + external-delivery approval; enforce information barriers.

## Reproducibility
`brief_id` binds output to the exact client context, instrument, and policy version.
