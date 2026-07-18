# Controls — investment-committee-memo-builder

- **Risk tier:** R2 — analytical / drafting support (no binding decision). **Action mode:**
  Draft-only; no system-of-record change.
- **Human approval:** `external-delivery` — human approval is required before the memo is
  circulated to the committee (external delivery) or written to any system of record.
  Internal analytical iterations may be reviewer-sampled.

## Prohibited (fail closed)

- **Making or recording the investment decision** or the committee vote. `committee_decision`
  stays `pending`; `validate_output` fails on any other value.
- **Sending, circulating, emailing, submitting, or marking the memo final.** Draft only.
- **Fabricating** any figure, comp, or claim; **restating** a figure the model does not
  support (tie-out break).
- **Unsupported / unapproved claims** — any assertion without a resolvable `source_id`, or a
  `market`/`research` source not marked approved.
- **Personalized investment advice** or guarantee / "risk-free" / "can't-lose" language.
- **Omitting** the mandatory downside case or known material risks.

## Draft states (this skill may set only these)

`drafting` → `needs-data` (missing/unapproved inputs) | `draft-ready` (validated, approvals
recorded, awaiting committee). It may **not** set `approved`, `declined`, `committed`,
`circulated`, or `filed`.

## Required output screens (`scripts/validate_output.py`)

1. All nine required template sections present and non-empty (template fidelity).
2. Every assertion resolves to a source; external (market/research) sources are approved.
3. Model/scenario/sizing tie-outs hold; downside present; base ties to the model; position
   within the single-name limit; no open block-severity flag.
4. `preparer` and `reviewer` approvals are **recorded**.
5. `committee_decision` == `pending`.
6. No prohibited language (advice/guarantee, premature delivery, or recorded decision).
7. Standing draft-only note present.

## Segregation of duties

Drafting (this skill) is distinct from **review**, from **approval**, and from the
**committee decision**. The same person must not both prepare and record the reviewer
sign-off; the committee decision is made by the committee, never by the drafter or the skill.

## Data classification, privacy, records

- **Highly Confidential (MNPI / client-confidential).** Deal materials are frequently MNPI;
  restrict access to the deal team + committee, honor information-barrier / wall-crossing
  controls, and never disclose deal existence or terms outside the entitled group.
- Retain the draft, its traceability appendix, source citations, and the template/limit-config
  versions with the deal record. Log every source read and every draft generation with the
  preparer identity for recertification and audit.
