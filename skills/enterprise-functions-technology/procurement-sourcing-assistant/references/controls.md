# Controls — procurement-sourcing-assistant

- **Risk tier:** R2 — analytical / drafting support. **Action mode:** Draft-only; no
  system-of-record change. The output is a draft sourcing pack for human review, not an award,
  an RFP issuance, or a supplier selection.
- **Human approval:** `external-delivery` — a human must review and approve before the pack is
  delivered, relied on for an award decision, or treated as a system-of-record change. Internal
  analytical assembly may be reviewer-sampled.

## Prohibited (fail closed)

- **Award / supplier selection / sourcing decision**: awarding a contract, naming a winning
  bidder, selecting a supplier, or any statement of a final or binding sourcing decision. The
  award is the committee's / sourcing lead's.
- **RFP issuance / delivery**: issuing, sending, publishing, or distributing an RFP/RFI, or
  notifying bidders. Draft-only.
- **Negotiation / commitment**: negotiating price or terms, committing spend, issuing a purchase
  order, or entering a binding commitment.
- **Vendor-risk / legal determinations**: making the third-party, cyber, or AI-vendor risk
  finding, or a legal/contractual determination. These are routed to the specialist skills and
  their owners.
- **Fabrication**: inventing a requirement, supplier, score, approval, or citation. Missing items
  are open items or `needs-data`.
- **Autonomous knockout**: eliminating a bidder without human confirmation. A mandatory
  requirement that appears unmet is a `knockout-flag`, not an elimination.

## Pack / bidder states (this skill may set only these)

Per bidder: `scored` | `knockout-flag` | `needs-data`. Per pack:
`draft-assembled` only, with `award_decision: pending-human-approval`. It may **not** set
`awarded`, `selected`, `issued`, `final`, or `submitted`.

## Required output screens (`scripts/validate_output.py`)

- All required template sections present (mirrors [../assets/output-template.md](../assets/output-template.md)).
- Every asserted entry (`captured`/`identified`/`scored`/`knockout-flag`/`drafted`/`routed`)
  carries a citation (no unsupported or unapproved claims).
- Each bidder's stated `weighted_score` ties out to the `evaluation_criteria` weights and the
  bidder's per-criterion scores (no fabricated numbers).
- Recorded approvals carry `type`, `approver_role`, `date`, and `citation`; missing required
  approvals appear as outstanding open items; `human_approval_required_before_delivery` is `true`.
- No award/selection, RFP-issuance/send, or negotiation/commitment language.
- `pack_status` equals `draft-assembled`; `award_decision` equals `pending-human-approval`.
- Standing note present: "Draft sourcing pack for human review only. This pack ranks bidders and
  recommends a preferred option for approval; it makes no sourcing decision, creates no
  purchasing commitment, and has not been issued, sent, or negotiated. Any award, delivery, or
  negotiation is a separate, human-approved step."

## Segregation of duties

Sourcing-pack assembly entitlements are distinct from vendor-risk assessment, legal review, and
the award decision. The same person/skill must not both assemble the pack and make the award or
the vendor-risk determination.

## Data classification, privacy, records

- **Confidential.** Bidder responses, pricing, and supplier commercials are competitively
  sensitive — restrict to the sourcing team and named approvers; never disclose one bidder's
  response to another.
- Mask supplier/sponsor identifiers to what the pack requires.
- Retain the pack manifest, citations, and config/template versions per the enterprise
  procurement recordkeeping policy; log the analyst identity on every read and assembly.
- Keep data within the deployment's residency boundary.
