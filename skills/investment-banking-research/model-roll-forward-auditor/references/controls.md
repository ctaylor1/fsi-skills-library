# Controls — model-roll-forward-auditor

- **Risk tier:** R2 — analytical/model support. **Action mode:** Draft-only; no system-of-record
  change.
- **Human approval:** `external-delivery` — external delivery requires human sign-off; no
  valuation opinion or model approval is ever made.

## Prohibited (fail closed)
- No **valuation / fair-value opinion**.
- No **model approval / validation / correctness confirmation**.
- No **assumed continuity** for a missing balance; no invented tolerance.

## Required output screen (`scripts/validate_output.py`)
- Per item: `residual == current_opening − prior_ending` (within tolerance).
- No valuation/approval language (regex: model is approved/we approve the model/fair value
  is/valuation is/the model is correct/sign off on the model/model is validated).
- Suggested disposition is review-only (`tied` | `breaks-for-review`).
- Standing disclaimer present.

## Segregation of duties
The auditor/analyst is not the model owner or the valuation authority; the audit supports, never
replaces, model sign-off and valuation judgment.

## Data classification, privacy, records
- **Highly Confidential (MNPI / client-confidential).** Enforce information barriers; deal-team
  only.
- Retain audit + citations + versions; log read + external-delivery approval.

## Reproducibility
`audit_id` binds output to the exact two model versions and tolerances; computation is
deterministic and stdlib-only.
