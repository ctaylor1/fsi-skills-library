# Controls — claims-fraud-referral-assistant

- **Risk tier:** R3 — regulated/control decision support. **Action mode:** Draft-only; no
  system-of-record change (routing to SIU is a *proposed* handoff via the approval broker).
- **Human approval:** `required` — a licensed SIU investigator / adjuster adjudicates every
  referral. This skill assembles evidence and a recommendation; it decides nothing.

## Prohibited (fail closed)

- **Fraud finding / determination** of any kind (indicators are red flags, not conclusions).
- **Adverse customer decision**: claim denial, closure, rescission, or policy voiding.
- **Acting for SIU**: recording a referral as accepted, or a disposition/"no further action".
- **Accusatory customer-facing text** revealing or asserting suspected fraud (defamation risk).
- **Indicators outside the approved `FR-*` catalogue**, or any un-cited indicator.
- **Sending/submitting** the referral — the skill drafts; a human transmits.

## Recommendation states (this skill may set only these)

`refer-to-siu` | `monitor` | `insufficient-indicators` | `needs-data`. It may **not** set a
fraud-confirmed, denial, closure, void, or SIU-accepted state.

## Required output screens (`scripts/validate_output.py`)

- Only allowed recommendations appear; no fraud-finding/denial/closure/void states.
- Every triggered indicator ID is from the approved catalogue and carries evidence + citation.
- `score_band` equals the deterministic mapping (with the prior-SIU override), evaluated with
  the effective band thresholds the engine records on the output (`indicator_config`) so a
  non-default deployment config ties out instead of being false-rejected against fixed defaults.
- Each `refer-to-siu` referral has a complete, cited `referral_package` and a drafted
  `referral_document` containing all required template sections (template fidelity).
- Required human approvals are recorded as **pending/required** — never auto-granted.
- No unsupported-claim, adverse-decision, or accusatory customer-facing language — including an
  affirmative fraud finding in plain phrasing ("this is fraud", "the claim is a fraud", "clearly
  fraud", "is a fraudster"), which fails closed just like the explicit "confirmed fraud" forms.
- Standing note present (draft-only; no finding, no denial/closure, no adverse decision).

## Segregation of duties

Drafting a referral is distinct from SIU investigation and from claim adjudication. The same
person/skill must not both draft the referral and adjudicate fraud or the coverage/claim.

## Data classification, privacy, records

- **Highly Confidential (customer NPI/PII).** Mask insured/claimant identifiers to what
  evidences the indicator; do not expose full identifiers in the referral body.
- Retain referral drafts, indicator evidence, and citations with the indicator-config version
  per the insurer's anti-fraud recordkeeping; log adjuster identity on every read and draft.
- Fraud referrals may carry legal-privilege and anti-defamation sensitivity — treat drafts as
  restricted work product for SIU, not customer-facing communications.
