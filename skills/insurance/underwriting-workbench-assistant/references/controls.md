# Controls — underwriting-workbench-assistant

- **Risk tier:** R3 — regulated / control decision support. **Action mode:** Draft-only; no
  system-of-record change. The compiled workbench profile is a draft deliverable a human
  underwriter reviews and acts on.
- **Human approval:** `required` — before any bind, quote, decline, issuance, referral
  disposition, or policy-administration write. This skill proposes and packages; a licensed
  human underwriter decides.

## Prohibited (fail closed)

- **Binding, quoting, declining, or issuing** coverage; setting price/terms as final.
- Making or communicating an **autonomous underwriting decision** ("approved", "declined",
  "bound", "issued").
- **Writing a system of record** (policy administration) or marking a case closed/filed.
- **Unsupported or unapproved claims** — every material assertion in the profile carries a
  citation; anything not sourced is listed as a gap, never asserted.
- **Guessing missing data** to complete a profile — incomplete/stale-critical data sets
  `needs-data`.
- Personalized coverage advice to the insured; that is the licensed underwriter's role.

## Dispositions (this skill may set only these — all advisory)

`needs-data` | `refer-to-underwriter` | `ready-for-underwriter-review`.

It may **not** set `bound`, `quoted`, `declined`, `issued`, `approved`, `closed`, or
`filed`. Every disposition is decision support pending human adjudication.

## Required output screens (`scripts/validate_output.py`)

- Only the three advisory dispositions appear (no bind/quote/decline/issue/close states).
- Every rule finding carries evidence; `decision_rationale.unsupported_claims` is empty; the
  recommendation is framed "for underwriter adjudication".
- `human_adjudication` is present and **pending**, with `decision: null` (no autonomous
  decision recorded).
- The packaged deliverable contains every required output-template section (see
  [../assets/output-template.md](../assets/output-template.md)).
- No coverage-binding / decision / filing / system-of-record language anywhere in the
  profiles.
- The standing note is present.

Any miss fails closed (exit 1). The bad fixture `evals/files/profile_bad.json` exercises the
screen and must fail.

## Segregation of duties

Compiling the workbench profile (this skill) is separate from the underwriting **decision**.
The same actor must not both compile the draft and record the binding decision without the
approval broker. Referrals go to a senior underwriter / referral authority per delegated
authority limits.

## Data classification, privacy, records

- **Highly Confidential (customer NPI/PII).** Mask insured identifiers to what the profile
  requires; do not surface raw PII where a masked reference suffices.
- Retain the compiled profile, citations, applied rule IDs, and `config_version` for
  underwriting-file recordkeeping and audit; log the compiling identity and the underwriter
  of record on adjudication.
- No external delivery from this skill; the draft stays in the underwriting workbench.
