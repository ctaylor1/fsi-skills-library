# Controls — company-profile-builder

- **Risk tier:** R2 — analytical / drafting support. **Action mode:** Draft-only; no
  system-of-record change. The profile is a draft artifact for human review.
- **Human approval:** `external-delivery` — internal analytical drafting may be
  reviewer-sampled; **before any external distribution or system-of-record change** a
  supervisory/research analyst **and** compliance (control room) must approve, and a human
  distributes via the approval broker.

## Prohibited (fail closed)

- **Distribution / delivery** — never send, submit, email, publish, or share the profile.
- **Investment advice / rating / recommendation / price-target opinion** — a profile states
  facts, not a view.
- **Unsupported assertions** — no fact may appear in a section without a citation.
- **MNPI in an external profile** — material non-public information is excluded from any
  externally distributed profile absent documented wall-crossing / compliance clearance.
- **Fabrication** — a missing or unsourced fact is an open item, never invented.
- **Auto-merge** of mismatched company identities.

## Assembly states (this skill may set only this)

`draft-assembled` — a review-ready draft with an open-items list. It may **not** set
`reviewed`, `approved`, `cleared`, `final`, `distributed`, or `delivered`; those are
human/compliance-owned states reached via the approval broker.

## Required output screens (`scripts/validate_output.py`)

- All required template sections present (`profile_summary`, `business_overview`,
  `key_financials`, `ownership`, `management`, `trading_data`, `transactions`, `sources`).
- **No unsupported assertions**: every section entry carries a citation and an asserted
  status (`included` | `stale` | `unresolved`); no unsourced fact is asserted.
- **No MNPI** on any section entry when `intended_distribution` is `external`.
- Required approvals recorded (role + date + citation); delivery approval flagged required;
  required-but-missing approvals appear as outstanding open items.
- No investment-advice / rating / recommendation language (regex: "we recommend",
  "our recommendation", "investment recommendation", "buy rating", "sell rating",
  "strong buy", "strong sell", "rated buy/sell", "should buy/sell/invest", "price target").
- No distribution / delivery language (regex: "sent to", "submitted to", "delivered to",
  "distributed to", "released to", "emailed to", "shared with the client", "we have sent").
- `assembly_status` is `draft-assembled`; standing note present.

## Segregation of duties

Drafting the profile is distinct from approving it and from distributing it. The analyst who
assembles the draft does not self-approve external delivery; supervisory-analyst and
compliance sign-off and human distribution are separate control steps.

## Data classification, privacy, records

- **Highly Confidential (MNPI / client-confidential).** Information-barrier controls apply;
  MNPI is gated as above.
- Mask internal company identifiers to what the profile needs; public identifiers
  (legal name, ticker) may appear.
- Retain the manifest, open items, approvals, and citations with template/config versions;
  log analyst identity on every read and assembly.
