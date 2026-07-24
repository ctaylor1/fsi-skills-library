# Controls — actuarial-data-lineage-checker

- **Risk tier:** R2 — analytical. **Action mode:** Draft-only; no system-of-record change.
- **Human approval:** `external-delivery` — before external delivery or a system-of-record write.

## Prohibited (fail closed)
- No **alteration/correction** of source data (the data owner acts).
- No **selection of actuarial assumptions or methods**; no model run.
- No **certification of reserve data** or actuarial opinion.
- No **inferring** missing values or dividing by a zero prior.

## Required output screen (`scripts/validate_output.py`)
- Every break carries a cited record/definition reference.
- No data-alteration / assumption-selection / certification language (regex: corrected the
  data/adjusted the source/set the assumption/selected the method/certified the reserve/reserve
  data is certified).
- Disposition is review-only (`clean` | `breaks-for-review`).
- Standing disclaimer present.

## Data classification, privacy, records
- **Highly Confidential (customer NPI/PII).** Mask policy/claim identifiers.
- Retain packet + citations + config/definition versions; log read + external-delivery approval.

## Reproducibility
`lineage_id` binds output to the exact datasets, definition versions, and config version.
