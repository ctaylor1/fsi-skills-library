# Controls — payment-integration-readiness-pack

- **Risk tier:** R3 — regulated/control decision support. **Action mode:** Draft-only; no
  system-of-record change.
- **Human approval:** `required` — for any go-live approval or launch clearance.

## Prohibited (fail closed)
- No **go-live approval**, **launch clearance**, or **production-ready** declaration.
- No **assumption of readiness** for a missing attestation; no acceptance of an unjustified N/A.
- No **change** to attestations or config.

## Required output screen (`scripts/validate_output.py`)
- Every gap carries a cited item + checklist version.
- No go-live/launch/approval language (regex: approved for go-live/cleared to launch/is
  production-ready/go live now/launched the integration/approve go-live).
- Suggested disposition is review-only (`ready-for-review` | `gaps-for-review`).
- Standing disclaimer present.

## Segregation of duties
The packager/manager is not the go-live approver; the packet supports, never replaces, the
authorized approver and the launch process.

## Data classification, privacy, records
- **Highly Confidential (cardholder data / PCI + NPI/PII).** Mask merchant/account identifiers.
- Retain packet + citations + checklist version; log read + external-delivery approval.

## Reproducibility
`packet_id` binds output to the exact attestations and checklist version.
