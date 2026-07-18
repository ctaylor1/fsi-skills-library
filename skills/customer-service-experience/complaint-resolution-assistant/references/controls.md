# Controls — complaint-resolution-assistant

- **Risk tier:** R2 — analytical / drafting support. **Action mode:** Draft-only; no
  system-of-record change.
- **Human approval:** `external-delivery` — a complaints handler makes the uphold/reject
  decision and an approver signs off before **any** external delivery, redress payment, or
  system-of-record change. Internal drafting may be reviewer-sampled.

## Prohibited (fail closed)

- **Sending / submitting** the response, or contacting the customer.
- **Executing** a refund, payment, account change, or fee reversal.
- **Filing** a regulatory complaints return or **closing** the complaint.
- **Binding decisions**: the final uphold/reject determination or any admission of **legal
  liability**.
- **Unsupported claims**: guarantees, promises of a specific result, disparagement, or
  **legal/financial advice** (e.g., telling the customer to sue).

## Dispositions (this skill may set only these)

`draft-ready` | `refer-specialist` | `needs-data` | `needs-review`. It may **not** set
`decided`, `upheld-final`, `sent`, `closed`, or `filed`. `proposed_outcome`
(`uphold` | `partial-uphold` | `not-upheld` | `needs-review`) is a **recommendation**, never a
decision.

## Required output screens (`scripts/validate_output.py`)

- Only allowed dispositions and proposed outcomes appear.
- Every draft letter contains all required template sections + the DRAFT marker.
- Required approvals are recorded: `complaints_handler_review`, `final_response_approver`.
- Remediation ties out (components sum to total); goodwill within the config cap.
- No unsupported/unapproved-claim language (liability admission, guarantee, promise, legal
  advice, executed-payment).
- No send/submit/file/close language.
- Standing note present: "Draft complaint response only … Nothing has been sent to the
  customer or reported to a regulator."

## Segregation of duties

Drafting is distinct from deciding, delivering, and reporting. The person/skill that drafts
must not be the sole approver of the decision or the executor of the redress payment.

## Data classification, privacy, records

- **Highly Confidential (customer NPI/PII).** Mask customer identifiers to what evidences the
  complaint; restrict draft outputs to the handling team.
- Retain draft packages, remediation working, and citations with the config/standards
  versions used; log the drafter identity on every read and draft.
- Assess against effective-dated terms in force at the time of the events.
