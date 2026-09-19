# Controls — insurance-rating-worksheet-builder

- **Risk tier:** R3 — regulated/control decision support. **Action mode:** Draft-only; no
  system-of-record change.
- **Human approval:** `required` — for any binding, quote issuance/finalization, or offer.

## Prohibited (fail closed)
- No **binding coverage**, **issuing/finalizing a quote**, or **making an offer**.
- No **overriding the rate manual**; no **inventing a factor** value.
- No **hiding the minimum-premium** floor; no assuming a missing base rate.

## Required output screen (`scripts/validate_output.py`)
- Per coverage: `premium_before_fees == base_rate × Π(factor values)` (within tolerance).
- Total: `indicated_premium == Σ coverage_total + policy_fees` (within tolerance).
- No bind/quote-issuance language (regex: bound the coverage/coverage is bound/we issue the
  quote/policy issued/quote is final/we bind/offer of coverage extended).
- Standing disclaimer present.

## Segregation of duties
The rating analyst is not the binding/quoting authority; the worksheet supports, never replaces,
underwriting's binding and quoting.

## Data classification, privacy, records
- **Highly Confidential (customer NPI/PII).** Mask policy/insured identifiers.
- Retain worksheet + manual version; log read + external-delivery approval.

## Reproducibility
`worksheet_id` binds output to the exact rate-manual version and risk characteristics; computation
is deterministic and stdlib-only.
