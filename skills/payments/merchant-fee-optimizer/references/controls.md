# Controls — merchant-fee-optimizer

- **Risk tier:** R2 — analytical. **Action mode:** Read-only analysis.
- **Human approval:** `external-delivery` — required before the pack goes to the merchant
  client or is written to a case/system of record.

## Prohibited (fail closed)

- No **guarantee of savings** or firm promise of an outcome ("guaranteed", "risk-free",
  "you will save X"). Savings are **estimates with stated assumptions**, always a range.
- No **binding commercial decision or directive**: do not tell the merchant to sign,
  terminate, cancel, or switch a processor or contract; present options and route the
  decision to a human.
- No **legal, tax, or accounting advice**, including opinions on contract enforceability or
  whether a term is void — surface contract terms factually and defer to counsel.
- No **benchmark tuning to the individual**; use only the versioned config benchmarks.
- No **write** to any processor, contract, ledger, or settlement system of record.

## Required output screens (`scripts/validate_output.py`)

- Every fired opportunity has ≥ 1 cited evidence row and ≥ 1 stated assumption.
- Every fired opportunity is a **range** (`est_savings_low ≤ est_savings_high`, both ≥ 0)
  and is **not** flagged `guaranteed`.
- `total_estimated_savings` **ties out** to the sum of fired opportunities, and annual =
  12 × monthly (no double counting; reproducible).
- No prohibited/binding-language (regex screen: `guarantee(d)`, `risk-free`, `you will save`,
  `we recommend switching/terminating/…`, `terminate the contract`, `sign the contract`,
  `legally binding/void`, `this is legal advice`, etc.).
- Standing disclaimer present: "Estimated savings and analysis only … not a guarantee of
  savings and not a recommendation to sign, terminate, or change any processor or contract …"

## Conduct / fairness

- Present card-mix observations factually; do not steer a merchant to surcharge, cash-
  discount, or steer cardholders in ways that may violate network rules or law — flag those
  as items for the merchant's own compliance/legal review, not recommendations.
- Do not overstate savings; frame the low band as the conservative floor and the point
  estimate as the ceiling.

## Data classification, privacy, records

- **Highly Confidential (customer NPI/PII; cardholder data).** Mask the MID and any PAN to
  last 4; never emit full card numbers. Operate on de-identified transaction detail only.
- Minimize data in the output to what evidences an opportunity.
- Retain the analysis + citations + config version per records policy; log the read and any
  external-delivery approval.

## Reproducibility

`analysis_id` binds the output to the exact statement period, inputs, benchmarks, and
**config version**; re-running with the same inputs and config reproduces the decomposition,
opportunities, and estimate ranges.
