# Controls — fnol-normalizer

- **Risk tier:** R3 — regulated/control decision support. **Action mode:** Read-only analysis.
- **Human approval:** `required` — for any coverage/liability/reserve determination or claim
  open/route action.

## Prohibited (fail closed)
- No **coverage** determination; no **liability/fault** assignment; no **reserve** setting.
- No **opening, routing, or adjudicating** a claim as an action.
- No **guessed mapping** for an unmappable code; no fabricated required value.

## Required output screen (`scripts/validate_output.py`)
- Every exception carries a cited raw-field reference.
- No coverage/liability/reserve/adjudication language (regex: coverage is/covered under/deny
  coverage/assign liability/at fault/set the reserve/open the claim).
- Suggested disposition is review-only (`normalized` | `exceptions-for-review`).
- Standing disclaimer present.

## Segregation of duties
The normalizer is not the adjuster; the record supports intake, never replaces claims
adjudication.

## Data classification, privacy, records
- **Highly Confidential (customer NPI/PII).** Mask claimant identifiers.
- Retain normalized record + mapping log + config version; log read + external-delivery approval.

## Reproducibility
`normalization_id` binds output to the exact raw record and vocabulary version.
