# Controls — model-roll-forward-auditor

## Version 0.2.0 contract

The native result is a closed calculation record. Retain the original input separately and validate with `python3 scripts/validate_output.py RESULT.json --input ORIGINAL.json`; `--selftest` loads both bundled examples. Computation validates input first. Finite JSON numbers, valid dates, supported domains and unique identifiers are enforced; duplicate JSON keys are rejected. Output validation reconstructs from the original and rejects omitted, altered or extra results, including flags/counts/statuses. Keep author narrative and workflow envelopes outside the native result. Source binding establishes deterministic fidelity to supplied inputs, not source authenticity, data rights, economic validity, institutional acceptance or independent assurance.

Retained through Phase 1 until shared-check and future reviewer parity is established. This is a supplied-balance continuity checker only: it does not read/update a workbook, compare formulas, assess assumptions or provide independent assurance. Require unique line items, model version IDs, explicit balances (null means structural break) and nonnegative explicit tolerances. A tied subset does not establish model correctness.


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
