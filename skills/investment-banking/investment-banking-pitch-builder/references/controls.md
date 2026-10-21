# Controls - investment-banking-pitch-builder

- **Risk tier:** R2 - analytical / drafting support. **Action mode:** Draft-only; no
  system-of-record change. The skill assembles a draft deliverable; it stages nothing for
  execution and performs no delivery.
- **Human approval:** `external-delivery` - a banker/MD, control-room/compliance, and
  legal/disclaimer sign-off must be **recorded** before the draft may be marked
  `approved-for-delivery`, and the actual delivery to any external party is performed by a
  person, never by this skill.

## Prohibited (fail closed)

- **Sending, submitting, distributing, emailing, or filing** materials, or marking the
  draft as `sent`/`delivered`/`submitted`/`distributed`/`filed`.
- **Fabricating** any figure, chart, or source; including a claim without an **approved**
  `source_ref`.
- **Unsupported assertions** - promissory/guarantee/superlative-without-source language
  ("guaranteed", "risk-free", "will outperform", "assured returns", "you should buy/sell").
- **Personalized investment, legal, or tax advice.**
- Marking `approved-for-delivery` without all required approvals recorded and approved.

## Delivery states (this skill may set only these)

`draft` -> `hold-for-approval` -> `approved-for-delivery`. It may **not** set `sent`,
`delivered`, `submitted`, `distributed`, `filed`, or any state implying the materials left
the firm. `approved-for-delivery` means humans cleared the draft for a person to deliver.

## Required output screens (`scripts/validate_output.py`)

- Every required template section is present (template fidelity / completeness).
- Every page has a takeaway and at least one cited source; every claim has an approved
  `source_ref` (source mapping / no unsupported assertions).
- No promissory/guarantee/advice language anywhere in titles, takeaways, or claims.
- Each required approval role is recorded; `approved-for-delivery` only when all approved.
- Draft-only notice and standing note present; `delivery_status` is never a delivered state.

## Segregation of duties

The **preparer** (analyst/banker assembling the draft) is distinct from the **approvers**
(deal-captain MD sign-off, control-room/compliance clearance, legal/disclaimer review). The
same person must not both assemble and self-approve the required control approvals.

## Data classification, privacy, records

- **Highly Confidential (MNPI / client-confidential).** Pitch materials routinely contain
  material non-public information; **information-barrier / wall-cross and control-room
  clearance** apply. No selective disclosure; distribution only to cleared recipients by a
  person.
- Retain the draft, its source map, the template `id@version`, and the approval records for
  the engagement per records policy; log preparer identity and every approval.
