# Controls — order-allocation-validator

- **Risk tier:** R3 — regulated/control decision support. **Action mode:** Read-only analysis.
- **Human approval:** `required` — for any allocation, amendment, booking, or compliance
  certification.

## Prohibited (fail closed)
- No **allocation, re-allocation, amendment, or booking** of an order.
- No **override** of eligibility/entitlements; no assumption of a missing policy.
- No **compliance certification** ("allocation is compliant") — evidence only.
- No **rationalizing** an undocumented deviation.

## Required output screen (`scripts/validate_output.py`)
- Quantities tie (Σ allocated == executed qty) or a break is flagged for routing.
- Every exception carries a cited evidence line + policy rule/version.
- No allocation-decision/amendment/approval language (regex: allocate/re-allocate/amend the
  order/book the allocation/approved allocation/allocation is compliant/reallocat).
- Suggested disposition is review-only (`clean` | `exceptions-for-review`).
- Standing disclaimer present.

## Segregation of duties
The validator/analyst is not the allocation approver; the packet supports, never replaces, the
authorized reviewer.

## Data classification, privacy, records
- **Highly Confidential (customer NPI/PII).** Mask account numbers to last 4.
- Retain validation + citations + policy version; log read + external-delivery approval.

## Reproducibility
`validation_id` binds output to the exact allocation record and policy version.
