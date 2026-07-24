# Controls — liability-evidence-matrix-builder

- **Risk tier:** R3 — regulated/control decision support. **Action mode:** Read-only analysis.
- **Human approval:** `required` — for any liability, fault, negligence, or apportionment
  determination.

## Prohibited (fail closed)
- No **liability / fault / negligence** determination.
- No **apportionment** of responsibility; no **claim decision**.
- No **resolving** contradicting evidence; no inferring support for a bare fact.

## Required output screen (`scripts/validate_output.py`)
- Every matrix cell (supporting/contradicting) carries evidence citations.
- No liability/fault language (regex: is liable/at fault/we find fault/liability rests/assign
  liability/is negligent/breached the duty of care).
- Suggested disposition is review-only (`matrix-complete` | `gaps-for-review`).
- Standing disclaimer present.

## Segregation of duties
The matrix builder is not the adjuster; the bundle supports, never replaces, the adjuster's
liability evaluation.

## Data classification, privacy, records
- **Highly Confidential (customer NPI/PII, may include injury/medical).** Mask claimant identifiers.
- Retain matrix + citations; log read + external-delivery approval.

## Reproducibility
`matrix_id` binds output to the exact facts and evidence mapped.
