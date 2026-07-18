# Controls — chargeback-dispute-packager

- **Risk tier:** R2 — analytical / drafting support. No binding decision. **Action mode:**
  Draft-only; no system-of-record change.
- **Human approval:** `external-delivery` — a human must review and authorize before the
  representment is submitted to the acquirer/network or any system of record is changed.
  Internal drafting may be reviewer-sampled.

## Prohibited (fail closed)

- **Submission / filing / transmission** of the representment to any acquirer, card
  network, or portal. This skill drafts only; a human submits.
- **Fraud, liability, or "who wins" determination.** The skill assembles evidence and a
  rebuttal; the network/issuer decides the dispute.
- **Outcome guarantees** ("guaranteed win/reversal/refund", "you will win", "100% success").
- **Unsupported/unapproved claims** — any narrative assertion not backed by a bundled,
  identified exhibit.
- **Fabricated or altered evidence**, or a reason code not in the current network ruleset.
- **Personalized legal advice.**

## Package statuses (this skill may set only these)

`draft-representment` (packageable) | `insufficient-evidence` | `past-deadline` |
`identity-mismatch` | `unsupported-claim` | `needs-data`. It may **not** set `submitted`,
`filed`, `won`, `lost`, or `accepted`.

## Required output screens (`scripts/validate_output.py`)

- Every `reason_code` is a known/approved network code.
- A `packageable` record has `deadline_status == on_time`, complete evidence groups, a
  clean identity tie-out, and a fully supported narrative index.
- No guarantee/outcome language (regex): `guarantee(d) win/reversal/refund/recover`,
  `you will win`, `100% success`, etc.
- No submission language: `submitted to the network/acquirer`, `representment filed/sent`,
  `we have filed`, etc.
- No legal-advice language.
- Standing note present: the draft-only / no-submission / no-guarantee disclaimer.

## Deadline & evidence discipline

- The representment window is measured from the **chargeback date** using the current
  ruleset; a past-due dispute is flagged `past-deadline` and is **never** marked packageable.
- Evidence completeness is evaluated against the reason code's required-evidence **groups**
  (AND across groups, OR within a group). A missing group blocks packaging.

## Data classification, privacy, records

- **Highly Confidential (customer NPI/PII; cardholder data).** Never place full PAN in the
  package; mask to last four. Include only evidence necessary to rebut the reason code.
- Retain the draft package, the `ruleset_version`, evidence citations, and the reviewer
  sign-off with the case; log every read and every package produced with the analyst identity.
- PCI DSS scope applies to any cardholder data handled — minimize and mask.
