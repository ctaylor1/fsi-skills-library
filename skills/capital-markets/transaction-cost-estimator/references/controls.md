# Controls — transaction-cost-estimator

- **Risk tier:** R2 — analytical. **Action mode:** Draft-only; no system-of-record change.
- **Human approval:** `external-delivery` — before external delivery or a system-of-record write.

## Prohibited (fail closed)
- No **routing, execution, cancel, or amendment** of an order.
- No **venue / broker / algo selection or recommendation**.
- No **best-execution assertion** ("execution was best-ex / optimal / should have used venue X").
- No **invented impact coefficient** or benchmark; no division by zero/absent ADV.

## Required output screen (`scripts/validate_output.py`)
- Cost components sum to the reported total (bps) within tolerance; bps and currency agree.
- Methodology version present; every component cited.
- No execution/venue/broker/algo-advice or best-ex-assertion language (regex screen).
- Uncertainty range present for market impact.
- Standing disclaimer present.

## Data classification, privacy, records
- **Highly Confidential (customer NPI/PII).** Mask account/order identifiers.
- Retain TCA + citations + methodology version; log read + external-delivery approval.

## Reproducibility
`tca_id` binds output to the exact execution record, market inputs, and methodology version.
