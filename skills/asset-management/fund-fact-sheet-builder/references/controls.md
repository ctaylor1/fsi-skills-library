# Controls — fund-fact-sheet-builder

- **Risk tier:** R2 — analytical / drafting support. **Action mode:** Draft-only; no
  system-of-record change. The fact sheet is a draft artifact for human review.
- **Human approval:** `external-delivery` — internal analytical drafting may be
  reviewer-sampled; **before any external distribution or system-of-record change**, performance
  measurement verifies the numbers, compliance/marketing reviews the communication, a registered
  principal approves, and a human distributes via the approval broker.

## Prohibited (fail closed)

- **Distribution / delivery** — never send, submit, email, publish, or share the fact sheet.
- **Return promise or guarantee** — never state or imply guaranteed, risk-free, assured, or
  projected returns; past performance is not indicative of future results.
- **Investment advice / rating / recommendation** — a fact sheet states facts, not a view.
- **Unsupported assertions** — no figure may appear in a section without a citation.
- **Unreconciled figures** — no numeric figure may be asserted unless it ties to its
  system-of-record value within tolerance.
- **MNPI in an external fact sheet** — material non-public / embargoed information is excluded
  from any externally distributed sheet absent documented wall-crossing / compliance clearance.
- **Fabrication** — a missing or unsourced figure is an open item, never invented.
- **Auto-merge** of mismatched fund / share-class identities.

## Assembly states (this skill may set only this)

`draft-assembled` — a review-ready draft with a reconciliation ledger and an open-items list. It
may **not** set `verified`, `reviewed`, `approved`, `cleared`, `final`, `distributed`, or
`delivered`; those are human-owned states reached via the approval broker.

## Required output screens (`scripts/validate_output.py`)

- All required template sections present (`fund_summary`, `performance`, `holdings`, `risk`,
  `fees`, `esg`, `reconciliation`, `disclosures`, `sources`).
- **No unsupported assertions**: every content-section entry carries a citation and an asserted
  status (`included` | `stale` | `unresolved`); no unsourced figure is asserted.
- **Source-to-output reconciliation**: every asserted numeric figure with a source value ties
  out within tolerance; an unreconciled figure fails closed.
- **No MNPI** on any content entry when `intended_distribution` is `external`.
- Rendered disclosures carry approved text **and** a citation (no unsupported disclosure);
  required-but-missing disclosures appear as open items.
- Required approvals recorded (role + date + citation); delivery approval flagged required;
  required-but-missing approvals appear as outstanding open items.
- No performance-promise / guarantee language (regex: "guarantee(d)", "risk-free", "cannot
  lose", "no risk of loss", "will (out)perform", "assured returns", "projected to return/deliver").
- No investment-advice / rating / recommendation language (regex: "we recommend", "you should
  buy/invest", "buy this fund", "recommended for investors").
- No distribution / delivery language (regex: "sent to", "submitted to", "delivered to",
  "distributed to", "emailed to", "published to", "shared with the client").
- `assembly_status` is `draft-assembled`; standing note present.

## Segregation of duties

Drafting the fact sheet is distinct from verifying its numbers, approving it, and distributing
it. The analyst who assembles the draft does not self-verify performance, self-approve the
communication, or distribute; performance measurement, compliance/marketing, registered-principal
sign-off, and human distribution are separate control steps.

## Data classification, privacy, records

- **Highly Confidential (MNPI / client-confidential).** Information-barrier controls apply;
  MNPI/embargoed content is gated as above.
- Mask internal fund/account identifiers to what the fact sheet needs; public identifiers (legal
  name, ISIN, ticker) may appear.
- Retain the manifest, reconciliation ledger, open items, approvals, and citations with the
  template/config/disclosure versions; log analyst identity on every read and assembly.
