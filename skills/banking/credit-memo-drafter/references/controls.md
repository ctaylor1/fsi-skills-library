# Controls — credit-memo-drafter

- **Risk tier:** R3 — regulated/control decision support. **Action mode:** Draft-only; no
  system-of-record change. The memo is evidence + a recommendation; adjudication is human.
- **Human approval:** `required` — before any credit decision, pricing, exception/covenant
  disposition, booking, funding, filing, or system write. The draft records the required
  approver roles as **pending** and never grants them.

## Prohibited (fail closed)

- **Credit decision** of any kind — approve, decline, adverse action, or a pricing
  commitment.
- **Booking, funding, disbursement, or filing**; any write to a system of record.
- **Granting or waiving** a policy exception or covenant (exceptions are *documented* with
  mitigants only).
- **Self-granting an approval** (an `approvals` entry may only be `pending`/`required`).
- **Unsupported assertions** — any material figure without a cited source.
- **Guessing** a missing figure (missing grade/appraisal/spread line → `needs-data`).

## Disposition (this skill may emit only this)

`draft-for-underwriter-review`. It may **not** emit `approved`, `declined`, `booked`,
`funded`, `filed`, or any decision/closure state.

## Required output screens (`scripts/validate_output.py`)

- Disposition is the draft outcome only.
- Every required template section is present, non-empty, and cited (source-to-memo
  traceability); section keys match [../assets/output-template.md](../assets/output-template.md).
- `unsupported_assertions` is empty.
- `spread_tie_out.status == "tie"` (recomputed DSCR/leverage reconcile to the approved spread).
- `approvals` recorded and all still pending — no self-granted approval.
- No decision / closure / filing / booking / covenant-waiver language (regex screen).
- Standing draft-only note present.

## Segregation of duties

Drafting is distinct from underwriting/approval. The analyst or skill that drafts the memo
must not also adjudicate the credit, dispose of the exceptions, or book the facility.

## Data classification, privacy, records

- **Highly Confidential (customer NPI/PII).** Minimize and mask borrower identifiers; keep
  tax-return / statement detail to the figures cited.
- Retain the draft, citations, and policy/template versions per credit-file recordkeeping; log
  the analyst identity on every read and every draft.
