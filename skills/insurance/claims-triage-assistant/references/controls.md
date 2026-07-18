# Controls — claims-triage-assistant

- **Risk tier:** R3 — regulated / control decision support. **Action mode:** Draft-only; no
  system-of-record change. Severity, urgency, coverage questions, and routing are
  **recommendations with mandatory human adjudication**.
- **Human approval:** `required` — a claims triage lead reviews and a claims supervisor /
  adjuster of record signs off before **any** queue/adjuster assignment, reserve, coverage
  decision, payment, closure, or system-of-record change.

## Prohibited (fail closed)

- **Coverage determination** — deciding that a claim is (or is not) covered, or that an
  exclusion applies. Triage only *surfaces* coverage questions.
- **Reserve setting or change**, **claim approval/denial**, **payment/settlement**, and
  **claim closure**.
- **Assignment in the system of record** — assigning the claim to an adjuster or queue in the
  claims platform. Triage *recommends* a queue; a human assigns.
- **Fraud or liability conclusions** — fraud indicators are a referral signal only; liability
  is a human adjudication.
- **Sending/filing** — contacting the claimant, notifying a producer, or filing any
  regulatory report.

## Dispositions (this skill may set only these)

`draft-ready` | `refer-specialist` | `needs-data` | `needs-review`. It may **not** set
`assigned`, `covered`, `denied`, `approved`, `reserved`, `settled`, `closed`, or `filed`.
Severity/urgency bands and routing are **recommendations**, never decisions.

## Required output screens (`scripts/validate_output.py`)

- Only allowed dispositions appear.
- `severity_band` / `urgency_band` tie out to their documented scores.
- Every draft summary contains all required template sections + the DRAFT marker + citations.
- Required approvals are recorded: `triage_lead_review`, `claims_supervisor_approval`.
- No unsupported/unapproved-claim language (coverage determination, claim approve/deny/pay/
  close, reserve setting, fraud/liability conclusion, guarantee).
- No executed/send/assign/file/pay/close language.
- Standing note present: "Draft claims triage only … No coverage decision, reserve, payment,
  assignment, or claim closure has been made."

## Segregation of duties

Triage is distinct from adjudication, adjusting, and payment. The person/skill that triages
must not be the sole decision-maker on coverage, the setter of the reserve, or the executor
of payment. Fraud referral (SIU) and coverage analysis are separate control activities.

## Data classification, privacy, records

- **Highly Confidential (customer NPI/PII).** Mask policy/claimant identifiers to what
  evidences the triage; restrict draft outputs to the claims team.
- Retain triage records, recommended bands, coverage questions, and citations with the
  severity-map/config versions used; log the triager identity on every read and draft.
- Assess coverage questions against effective-dated terms in force at the date of loss.
