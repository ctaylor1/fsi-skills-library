# Controls — claim-settlement-authority-packet

- **Risk tier:** R3 — regulated/control decision support. **Action mode:** Draft-only; no
  system-of-record change.
- **Human approval:** `required` — for any settlement approval, authority grant, or payment
  authorization.

## Prohibited (fail closed)
- No **approving a settlement**, **granting/exercising authority**, or **authorizing payment**.
- No **setting/re-estimating** the settlement amount (exposure comes from the supplied evaluation).
- No **approving at the top tier** an exposure that exceeds the matrix — escalate instead.

## Required output screen (`scripts/validate_output.py`)
- Every completeness gap carries a citation; the required tier cites the matrix version.
- No approval/authority-grant/payment language (regex: settlement approved/authority granted/we
  approve the settlement/approved to settle/authorized the payment/settle at).
- Suggested disposition is review-only (`packet-ready` | `gaps-for-review`).
- Standing disclaimer present.

## Segregation of duties
The packet preparer is not the approver; the request supports, never replaces, the authorized
approver's decision. The required approver named is a **lookup**, not a delegation.

## Data classification, privacy, records
- **Highly Confidential (customer NPI/PII).** Mask claimant identifiers.
- Retain packet + citations + matrix version; log read + external-delivery approval.

## Reproducibility
`packet_id` binds output to the exact evaluation and matrix version.
