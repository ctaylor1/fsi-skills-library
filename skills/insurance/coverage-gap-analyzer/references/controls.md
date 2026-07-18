# Controls — coverage-gap-analyzer

- **Risk tier:** R2 — analytical. **Action mode:** Read-only analysis.
- **Human approval:** `external-delivery` — required before the analysis goes to a customer
  or a case/system of record. A licensed professional must review before any customer use.

## Prohibited (fail closed)

- No **coverage, eligibility, or claim determination** — never state or imply that a claim,
  loss, or event **is / is not / will be** covered, paid, denied, or eligible.
- No **personalized insurance, legal, or tax advice** and no recommendation to **transact**
  (buy, drop, cancel, switch, increase/decrease a specific policy). Surface gaps and
  questions; the licensed professional advises.
- No **adequacy verdict** ("you have adequate/sufficient coverage", "this policy is right
  for you"). Report the measured gap factually; do not conclude sufficiency.
- No **binding, quoting, or underwriting decision**; no premium indication presented as an offer.
- No **threshold tuning to the individual**; use only the versioned config.
- No **opaque scoring** presented as decisive; gaps are explainable, evidenced, and rule-based.

## Required output screens (`scripts/validate_output.py`)

- Every fired gap has ≥1 evidence row with **both** an exposure citation and a policy citation.
- `review_priority` equals the deterministic mapping from `fired_gaps`.
- No determination/advice language (regex screen: "you are covered", "this claim will be
  covered", "will be denied", "we cover/deny", "you have adequate coverage", "I recommend you
  buy/cancel/switch", "this policy is right for you", "eligible for", etc.).
- Standing disclaimer present: "Coverage-gap analysis only; not a coverage, eligibility, or
  claim determination and not insurance or legal advice. Consult a licensed insurance
  professional before acting."
- `review_prompts` (context a professional must weigh) included when any gap fired.

## Fairness / conduct

- Do not use protected-class attributes or proxies as inputs to any gap.
- Analyze the stated exposures and policy terms only; do not infer sensitive personal facts.
- Describe gaps factually; avoid alarmist or pressure language that steers a purchase.

## Data classification, privacy, records

- **Highly Confidential (customer NPI/PII).** Mask policy/account numbers to last 4.
- Minimize customer data in the output to what evidences a fired gap.
- Retain the analysis + citations + config version per records policy; log read + approval.

## Reproducibility

`analysis_id` binds the output to the exact inputs, the `as_of`, and the **config version**;
re-running with the same inputs and config reproduces the gaps and the review priority.
