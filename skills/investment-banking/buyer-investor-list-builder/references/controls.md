# Controls — buyer-investor-list-builder

- **Risk tier:** R2 — analytical / drafting support. **Action mode:** Draft-only; no
  system-of-record change. The output is an internal draft; nothing is sent, and no buyer is
  contacted.
- **Human approval:** `external-delivery` — a `deal_lead` and an independent
  `conflicts_reviewer` must be recorded in the approvals ledger and both `approved` before the
  list may be marked ready for external delivery, and the actual delivery/outreach is performed
  by a human. Internal analytical use may be reviewer-sampled.

## Prohibited (fail closed)

- **Sending, delivering, sharing, emailing, or publishing** the list to a client, counterparty,
  or any buyer.
- **Contacting, emailing, calling, approaching, or soliciting** any buyer/investor/sponsor —
  the skill plans outreach waves but never executes outreach.
- **Placing a restricted or conflicted candidate in an active outreach wave** — restricted-list
  members and unresolved-conflict candidates are held (`hold-conflicts-review`) and routed for
  clearance.
- **Unsupported assertions** — any fit-rationale or relationship claim without a resolvable
  citation to an indexed source is excluded (`needs-source`); a figure/claim is never asserted
  to fill a gap.
- **Investment recommendation, buy/sell advice, or valuation opinion** (e.g., "recommend we
  sell to X", "fair value is $Y", price target) — R2 makes no binding decision.
- **Filing or writing a system of record.**

## Dispositions (this skill may set only these)

`wave-1-priority` | `wave-2-standard` | `wave-3-broaden` (placed by documented fit score) |
`hold-conflicts-review` (restricted/conflict — excluded from waves) | `needs-data` (missing
scoring fields) | `needs-source` (no rationale resolves to an indexed source) | `duplicate`
(linked to a prior outreach-list entry). It may **not** set any "contacted", "delivered",
"sold", or "closed" state.

## Required output screens (`scripts/validate_output.py`)

- All 10 required template sections present.
- No unsupported claim in the delivered `buyer_list`: every listed candidate has ≥1 rationale
  item and every rationale item cites a `source_doc` resolving to the source index; no
  candidate recorded in `unsupported_claims` appears in the delivered list.
- Fit-score → outreach-wave tie-out for every wave-placed candidate.
- Restricted/conflict control: any `restricted`/`conflict` candidate is `hold-conflicts-review`
  and appears in **no** wave id-list.
- Required approvals recorded (`deal_lead`, `conflicts_reviewer`); `external_delivery` may be
  true only when both are `approved` with a date.
- No send/deliver/share/outreach-execution language; no recommendation/valuation-opinion/advice
  language; standing note present.

## Segregation of duties

List construction (this skill) is distinct from conflicts clearance (a compliance/control human
or `conflicts-of-interest-reviewer`) and from client delivery / outreach execution (the deal
team). The same actor must not both build the list and clear its own conflicts hold.

## Data classification, privacy, records

- **Highly Confidential — MNPI / client-confidential.** Treat the mandate, target, and buyer
  universe as material non-public information; apply information-barrier and need-to-know
  controls and never route content outside the deal team.
- Mask target/candidate identifiers to what the list requires.
- Retain the list, source index, citations, restricted-list version, and approval ledger per the
  engagement's records policy; log every read, draft, and approval with the analyst identity.
