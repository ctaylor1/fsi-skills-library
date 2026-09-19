# Controls — insurance-rate-form-filing-packager

- **Risk tier:** R3 — regulated/control decision support. **Action mode:** Draft-only; no
  system-of-record change.
- **Human approval:** `required` — for any submission, rate approval, or compliance
  certification.

## Prohibited (fail closed)
- No **submission or filing** with a regulator.
- No **rate approval** or setting; no assumption of a missing checklist.
- No **compliance certification** ("filing is compliant/approvable") — evidence only.
- No **rationalizing** an unsupported filed rate or a missing exhibit.

## Required output screen (`scripts/validate_output.py`)
- Every gap carries a cited evidence line + checklist rule/version.
- No submission/approval/certification language (regex: submit/filed the filing/filing is
  approved/filing is compliant/certify…compliant/binding).
- Suggested disposition is review-only (`ready-for-review` | `gaps-for-review`).
- Standing disclaimer present.

## Segregation of duties
The packager/analyst is not the filing approver or the regulator; the packet supports, never
replaces, the authorized reviewer and the regulatory process.

## Data classification, privacy, records
- **Highly Confidential (customer NPI/PII).** Mask policy/insured identifiers.
- Retain packet + citations + checklist version; log read + external-delivery approval.

## Reproducibility
`packet_id` binds output to the exact filing record and checklist version.
