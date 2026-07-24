# Controls — desk-pnl-risk-attribution-pack

- **Risk tier:** R3 — regulated/control decision support. **Action mode:** Draft-only; no
  system-of-record change.
- **Human approval:** `required` — for any P&L adjustment, restatement, booking, or sign-off.

## Prohibited (fail closed)
- No **adjusting, restating, or booking** P&L.
- No **sign-off / attestation / certification** of the P&L.
- No **approving** a break; no invented tolerance; no coercing a non-numeric component.

## Required output screen (`scripts/validate_output.py`)
- `explained + residual == reported_pnl` (within tolerance).
- No adjustment/sign-off language (regex: adjusted the p&l/we signed off/booked the
  adjustment/attest the p&l/certify the p&l/approve the p&l/restated the p&l).
- Suggested disposition is review-only (`tied` | `breaks-for-review`).
- Standing disclaimer present.

## Segregation of duties
The attribution analyst is not the P&L sign-off authority; the packet supports, never replaces,
product control's review and sign-off.

## Data classification, privacy, records
- **Highly Confidential (customer NPI/PII).** Mask desk/book identifiers as needed.
- Retain attribution + citations + tolerance version; log read + external-delivery approval.

## Reproducibility
`attribution_id` binds output to the exact P&L, components, and tolerance version; computation is
deterministic and stdlib-only.
