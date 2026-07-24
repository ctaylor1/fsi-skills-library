# Controls — claim-damage-evaluation-comparator

- **Risk tier:** R3 — regulated/control decision support. **Action mode:** Read-only analysis.
- **Human approval:** `required` — for any damages, reserve, settlement, coverage, or liability
  determination.

## Prohibited (fail closed)
- No **setting, valuing, or recommending** damages, reserve, or settlement amount.
- No **coverage or liability** determination.
- No **payment approval**; no netting/summing into a "recommended" figure.

## Required output screen (`scripts/validate_output.py`)
- Every finding carries item citations (items + documents).
- No valuation/settlement language (regex: set the damages/settlement value is/reserve should
  be/we value the claim/recommend settling/total damages are/approve payment).
- Suggested disposition is review-only (`clean` | `items-for-review`).
- Standing disclaimer present.

## Segregation of duties
The comparator/analyst is not the adjuster; the packet supports, never replaces, the licensed
adjuster's evaluation.

## Data classification, privacy, records
- **Highly Confidential (customer NPI/PII, including medical).** Mask claimant identifiers.
- Retain findings + citations; log read + external-delivery approval.

## Reproducibility
`comparison_id` binds output to the exact documents and line items compared.
