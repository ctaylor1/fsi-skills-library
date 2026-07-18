# Adjacent-Skill Handoffs — payment-failure-diagnoser

This skill produces a cited **payment diagnosis pack** (`diagnosis_id`) with a single
suggested route, and stops. It does not investigate to disposition, repair, file, or act.
The triage → investigation → repair chain is:

`payment-failure-diagnoser` / `iso-20022-message-interpreter` →
`payment-exception-investigator` → `payment-repair-assistant`

## Downstream (route the human/reviewer to)

| Downstream skill | When (root-cause category) | Handoff artifact |
| ---------------- | -------------------------- | ---------------- |
| `payment-exception-investigator` (R3) | `account_invalid`, `duplicate`, `system_timeout`, `screening_hold`, `recall_return`, `unknown` — stuck/ambiguous cases needing disposition | `diagnosis_id` + trace |
| `payment-repair-assistant` (R4) | `format_reference_error` — a fixable data/reference defect (BIC, account structure, reference, date) | `diagnosis_id` + decisive leg |
| `iso-20022-message-interpreter` (R2) | `message_unparseable` — the message itself needs field-level parsing/validation | message ref + `diagnosis_id` |
| `payment-fraud-case-investigator` (R3) | `suspected_fraud` — lost/stolen/suspected-fraud response codes needing investigation | `diagnosis_id` + focal payment |
| `dispute-operations-assistant` (R3) / `chargeback-dispute-packager` (R2) | `unauthorized_return` — customer/corporate unauthorized (`R05/R07/R08/R10/R29`) | decisive leg + trace |
| customer-remediation (no skill) | `insufficient_funds`, `expired_or_restricted`, `authorization_decline` — account-holder condition to resolve before any re-presentment | diagnosis summary |

## Upstream (may call this skill)

Service-desk and merchant-support skills, and `omnichannel-case-orchestrator`, may request a
diagnosis pack. A scheduled monitor is **not** used here (this skill is interactive,
`aws-fsi-scheduled-agent: no`).

## Duplicate-execution prevention

- This skill **diagnoses and routes only**; it must not repair, resubmit, reverse, release,
  refund, close a case, or file — those belong to the human and the downstream skills.
- Downstream skills reuse the `diagnosis_id` trace and root cause rather than re-tracing.
- Exactly **one** suggested route is emitted per diagnosis (the deterministic mapping),
  preventing conflicting parallel handoffs.
