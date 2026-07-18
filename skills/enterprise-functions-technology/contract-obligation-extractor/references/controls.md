# Controls — contract-obligation-extractor

- **Risk tier:** R2 — analytical / drafting support. **Action mode:** Draft-only; no
  system-of-record change. The output is a draft obligation register for human review, not a
  legal opinion, a certification, or a delivered document.
- **Human approval:** `external-delivery` — a human must review and approve before the
  register is delivered, relied on for a decision, or treated as a system-of-record change.
  Internal analytical extraction may be reviewer-sampled.

## Prohibited (fail closed)

- **Legal advice / interpretation**: enforceability, validity, breach determinations,
  liability, "you may terminate/renew/withhold", or any recommendation. These belong to
  licensed legal counsel.
- **Completeness / exhaustiveness claims**: any statement that all obligations have been
  captured, the register is complete/exhaustive, or the contract "contains no" / has "no
  further" obligations or restrictions. Absence of a clause is a `coverage-gap` to confirm,
  never an assertion of silence.
- **Unsupported assertions**: stating an obligation, date, or term without a clause citation.
  An extraction with no resolvable clause is `unsourced` and becomes an open item.
- **Delivery / execution**: sending, submitting, filing, transmitting, executing, signing, or
  delivering the register or the contract. Draft-only.
- **Fabrication**: inventing a clause, obligation, party, date, or term. Missing items are
  open items.

## Register states (this skill may set only these)

Per extraction: `extracted` | `ambiguous` | `conflict` | `coverage-gap` | `unsourced`.
Register: `draft-extracted` only. It may **not** set `certified`, `complete`, `final`,
`approved`, `executed`, or `delivered`.

## Required output screens (`scripts/validate_output.py`)

- All required template sections present (mirrors [../assets/output-template.md](../assets/output-template.md)).
- Every `extracted`/`ambiguous`/`conflict` entry carries a clause citation (no unsupported or
  unapproved claims).
- Recorded reviews carry `type`, `reviewer_role`, `date`, and `citation`; missing required
  reviews appear as outstanding open items; `human_approval_required_before_delivery` is `true`.
- No legal-advice/interpretation, completeness/exhaustiveness, or send/submit/execute/deliver
  language.
- `assembly_status` equals `draft-extracted`.
- Standing note present: "Draft obligation register for human review only. This register is an
  extraction aid, not legal advice or a completeness certification, and it has not been
  delivered, executed, or acted on. Every obligation must be verified against the source
  contract."

## Segregation of duties

Extraction entitlements are distinct from legal interpretation, obligation monitoring, and
external delivery. The same person/skill must not both extract the register and advise on,
certify, or deliver it.

## Data classification, privacy, records

- **Confidential.** Contracts routinely contain commercial terms, pricing, and counterparty
  and personnel identifiers. Mask person/user identifiers in output to what the register
  requires; do not expose pricing or personal data beyond the extracted term.
- Retain the register manifest, clause citations, and config/template versions per the
  organization's contract recordkeeping policy; log the analyst identity on every read and
  extraction.
- Keep data within the deployment's residency boundary.
