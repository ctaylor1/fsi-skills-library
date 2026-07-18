# Controls — policy-renewal-reviewer

- **Risk tier:** R2 — analytical. **Action mode:** Read-only analysis.
- **Human approval:** `external-delivery` — required before the comparison or any customer
  explanation goes to the insured/producer or a system of record.

## Prohibited (fail closed)

- No **renewal decision** or statement/implication that the policy **will** renew, non-renew, or be
  declined ("we will non-renew", "decline to renew", "the renewal is approved").
- No **pricing / rate action**: setting, quoting, or committing a premium, rate, or deductible
  ("set the premium at", "the new premium is/will be").
- No **binding** or **issuing a non-renewal / cancellation notice**.
- No **coverage or claim determination** ("deny coverage", "coverage is denied", "the claim is
  denied"); route claim questions to the claims function.
- No **personalized insurance advice** ("you should renew/switch/buy this option"); route to a
  licensed agent/broker.
- No **threshold tuning to the individual** insured; use only the versioned config.
- No **opaque scoring** presented as decisive; findings are explainable and evidenced.

## Required output screens (`scripts/validate_output.py`)

- Every fired finding has ≥1 cited evidence row.
- No determination / pricing / action / personalized-advice language (regex screen — see the pattern
  list in `validate_output.py`).
- `suggested_disposition` equals the deterministic mapping from the fired-finding set.
- Standing disclaimer present: "Comparison and review evidence only; not a renewal, pricing, or
  coverage determination. No renewal decision or notice has been issued."
- Context prompts included when any finding fired.

## Fairness / conduct

- Compare terms and describe changes factually; do not use protected-class attributes or proxies, and
  do not stigmatize the insured for their loss history.
- A premium change must be reported as a factual delta with the rate-vs-exposure divergence; do not
  attribute cause or intent — that is the underwriter's to explain.

## Data classification, privacy, records

- **Highly Confidential (customer NPI/PII).** Mask policy/account numbers to last 4.
- Minimize insured data to what evidences a fired finding.
- Retain the comparison + citations + `config_version` per records policy; log read + approval.

## Reproducibility

`review_id` binds the output to the exact inputs (both terms + loss history) and **config version**;
re-running with the same inputs and config reproduces the findings and disposition.
