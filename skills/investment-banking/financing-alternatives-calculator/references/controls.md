# Controls — financing-alternatives-calculator

- **Risk tier:** R2 — analytical/model support. **Action mode:** Draft-only; no system-of-record
  change.
- **Human approval:** `external-delivery` — external delivery requires human sign-off; no
  recommendation is ever made.

## Prohibited (fail closed)
- No **recommendation, ranking, or "cheapest/best/optimal"** labelling of any alternative.
- No **advice on which to choose**.
- No **assumed market rate** for a missing term; no combining mixed currencies.

## Required output screen (`scripts/validate_output.py`)
- Per debt row: `total_cost_over_term == annual_interest × term + upfront_fees` (within tolerance).
- No recommendation/ranking language (regex: we recommend/cheapest option/best option/should
  choose/optimal financing/go with the/is the winner).
- Standing disclaimer present.

## Segregation of duties
The calculator/analyst is not the advising banker; the worksheet supports, never replaces, banker
advice and the client's decision.

## Data classification, privacy, records
- **Highly Confidential (MNPI / client-confidential).** Enforce information barriers; deal-team
  only.
- Retain worksheet + terms + as_of; log read + external-delivery approval.

## Reproducibility
`calc_id` binds output to the exact terms and as_of; computation is deterministic and stdlib-only.
