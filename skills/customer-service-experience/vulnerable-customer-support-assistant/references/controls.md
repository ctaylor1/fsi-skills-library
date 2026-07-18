# Controls — vulnerable-customer-support-assistant

- **Risk tier:** R2 — analytical / drafting support. **Action mode:** Draft-only; no
  system-of-record change.
- **Human approval:** `external-delivery` — required before the assessment is shared beyond the
  handling agent, before any vulnerability marker or accommodation is recorded in the CRM, and
  before any referral is made. No approval is needed for the reviewing agent's own read.

## Prohibited (fail closed)

- No **diagnosis** — never state or imply the customer has a medical, mental-health, or
  cognitive condition ("has dementia", "suffers from depression", "diagnosed", "clearly has").
  A signal is context to support, never a clinical conclusion.
- No **mental-capacity or fitness determination** — never conclude the customer "lacks
  capacity", is "not competent", or "cannot manage their money". Capacity is a legal/clinical
  determination this skill must not make.
- No **discriminatory conclusion or service limitation** — never deny, restrict, or downgrade
  service, and never frame the customer, on the basis of a health condition, disability, age, or
  any protected characteristic.
- No **financial, investment, medical, or legal advice** — signpost to a licensed professional
  or an approved support organization instead.
- No **unsupported or unapproved suggestion** — an accommodation is suggested only when it is in
  the approved catalog and traced to a cited signal; a referral uses only an approved route.
- No **system-of-record change or customer contact** — the skill never records a marker, applies
  an accommodation, or sends anything to the customer.

## Required output screens (`scripts/validate_output.py`)

- Every observed signal carries a `source_ref` (no uncited assertion).
- Every suggested accommodation `code` is in the approved catalog and has ≥1 supporting cited
  signal (no unsupported/unapproved claim).
- Every suggested referral route (primary and additional) is in the approved route set.
- Required template sections are all present (template fidelity).
- No prohibited language: diagnostic, discriminatory / capacity-determination, or advice
  (regex screens over the rendered document and narrative).
- `record_update.mode == "proposed"` and `record_update.applied is false` (no autonomous SoR
  change; the marker/accommodation is a recorded proposal pending human approval).
- `human_review_required is true` (external-delivery approval gate).
- Standing note present (draft only; not a diagnosis; nothing applied or sent).

## Fairness / conduct

- Frame every signal and need respectfully and as current context, not as a fixed label.
- Do not use protected-class attributes or condition stigma in framing.
- Do not overstate a need; state what the customer signalled and what is still uncertain.
- Treat disclosed abuse or risk of harm as heightened: force the safeguarding referral route and
  a time-sensitive human-review flag — without diagnosing.

## Data classification, privacy, records

- **Highly Confidential (customer NPI/PII), including special-category data.** Mask identifiers
  to the last 4; minimize sensitive detail to the cited signal.
- Record special-category data only with a captured consent status; consent-dependent
  accommodations are marked `pending_consent` until consent is confirmed.
- Retain the assessment work-product + citations + config version per records policy; log the
  read and the external-delivery / record-change approvals. Never exfiltrate customer or health
  data.

## Reproducibility

`assessment_id` binds the output to the exact interaction inputs, the drivers taxonomy version,
and the accommodations-catalog version; re-running with the same inputs reproduces the signal
map, accommodations, and referral.
