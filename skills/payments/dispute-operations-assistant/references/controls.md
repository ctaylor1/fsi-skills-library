# Controls — dispute-operations-assistant

- **Risk tier:** R3 — regulated/control decision support. **Action mode:** Draft-only; no
  system-of-record change. The skill produces evidence + a recommendation + a drafted case
  response; a human adjudicates and authorizes any submission.
- **Human approval:** `required` — before any dispute decision, chargeback accept/deny,
  provisional/final credit, liability determination, response submission/filing, or case
  closure. Nothing here is autonomous.

## Prohibited (fail closed)

- **Dispute decision / adjudication**: accepting or denying a chargeback, deciding liability,
  or making a fraud finding.
- **Funds movement**: issuing provisional or final credit, refund, or write-off; any ledger
  or system-of-record posting.
- **Submission / filing / closure**: submitting or filing a response to a network, acquirer,
  or issuer; closing a case.
- **Self-authorization**: setting `authorization_status` to anything but
  `pending-human-authorization`, or `authorized_submission: true`.
- **Outcome guarantees / unsupported claims**: predicting a result or asserting a fact not
  backed by a bundled exhibit.
- **Personalized legal/financial advice** to a cardholder or merchant.

## Dispositions (this skill may set only these)

`draft-ready-for-review` | `evidence-insufficient` | `needs-data` | `out-of-time-review` |
`rule-version-stale` | `route-specialist`. It may **not** set `accepted`, `denied`,
`credited`, `submitted`, `filed`, `closed`, or `resolved`.

## Required output screens (`scripts/validate_output.py`)

- Only the allowed decision-support dispositions appear; role is issuer|acquirer; reason
  code present (role/transaction identity).
- Every `draft-ready-for-review` case has a complete draft package (all required template
  sections), an on-time/at-risk deadline, sufficient evidence, and a current rule version.
- Every draft carries citations; no unsupported/guarantee language.
- Human approval recorded and **not** self-granted (`pending-human-authorization`,
  `authorized_submission: false`).
- No decision/closure/filing/credit language anywhere (regex screen).
- Standing note present. Fail closed on any miss.

## Segregation of duties

Drafting dispute case-work is distinct from adjudicating the dispute, moving funds, and
submitting to the network. The same person/skill must not both draft and authorize the
submission. Fraud determination is a separate entitlement (`payment-fraud-case-investigator`).

## Data classification, privacy, records

- **Highly Confidential — customer NPI/PII and cardholder data (PCI DSS scope).** Never place
  full PAN in the package; mask to last four. Include only the evidence necessary for the
  reason code (data minimization).
- Retain the draft package, `current_rule_version`, evidence citations, and the human
  review/authorization record with the case; log every read and every draft produced with the
  analyst identity. Recertify per `aws-fsi-recertification-date`.
