---
name: buyer-investor-list-builder
description: >-
  Build and prioritize a buyer, investor, lender, or sponsor universe for a defined sell-side or
  capital-raise mandate: score each candidate against documented fit criteria, capture cited
  rationale and relationship context, screen against the firm restricted/conflicts list, and tier
  candidates into outreach waves. Use when a deal-team or coverage analyst needs to assemble a
  target-buyer or investor list, tier candidates into outreach waves, attach fit rationale and
  relationship context, or hand an approved list to process tracking or pitch materials.
  Draft-only HARD BOUNDARY: NEVER sends, delivers, or shares the list, NEVER contacts or initiates
  outreach to any buyer, NEVER files or writes a system of record, and NEVER makes a
  recommendation, valuation opinion, or investment advice. Every rationale must cite an approved
  source; restricted or conflicted candidates are held for review and excluded from active waves;
  external delivery requires recorded human approval; unsupported assertions fail closed.
license: MIT
compatibility: Amazon Quick Desktop; requires market/financial-data, filings, research-corpus, document-intelligence, and CRM MCP integrations plus the firm restricted/conflicts list (all read-only); drafting to a controlled workspace only - no external send or buyer contact.
metadata:
  aws-fsi-category: "Investment Banking & Research"
  aws-fsi-skill-type: "Artifact-creation skills"
  aws-fsi-risk-tier: "R2"
  aws-fsi-archetype: "Draft & package"
  aws-fsi-agent-pattern: "Interactive production copilot"
  aws-fsi-delivery-wave: "Wave 2 - analytical production"
  aws-fsi-action-mode: "Draft-only; no system-of-record change"
  aws-fsi-scheduled-agent: "no"
  aws-fsi-baseline-status: "new"
  aws-fsi-human-approval: "external-delivery"
  aws-fsi-data-classification: "Highly Confidential (MNPI / client-confidential)"
  aws-fsi-jurisdictions: "US (default); configure additional jurisdiction packs per deployment"
  aws-fsi-owner: "Investment Banking / Research"
  aws-fsi-primary-user: "Investment-banking / capital-markets analyst"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-07-17"
---

# Buyer / Investor List Builder

## Purpose and outcome
Turn a set of candidate acquirers, sponsors, lenders, or investors into a **prioritized,
source-mapped buyer list** for a defined mandate. For each candidate the skill computes a
documented fit score, attaches cited rationale and relationship context, screens the candidate
against the firm restricted / conflicts list, and tiers the placeable candidates into outreach
waves. The outcome is an internal draft keyed by a durable `list_id` — every rationale claim
ties to an indexed source — that a deal lead and a conflicts reviewer approve before any external
use. Conflicts clearance, client delivery, and buyer outreach stay with the human owners and
adjacent skills.

## Use when
- "Build / prioritize a buyer list for this sell-side mandate."
- "Assemble a sponsor and investor universe with fit rationale and relationship context."
- "Tier these candidates into outreach waves with reasons and sources."
- "Prepare the approved buyer universe to hand to process tracking or the pitch."

## Do not use
- **Delivering or sending the list, or contacting any buyer** → refuse; external delivery and
  outreach are human actions. Deal-process outreach/NDA/deadline tracking →
  `transaction-process-tracker`.
- **Clearing a conflict / restricted-list hit** → `conflicts-of-interest-reviewer` (this skill
  screens and holds; it never clears).
- **Building the model / valuation** (3-statement, DCF, LBO, merger, comps) → the modeling
  skills. This skill makes no valuation and no recommendation.
- **Company profile / strip page** → `company-profile-builder`; **industry map** →
  `market-landscape-researcher`.
- Any request to **send/deliver, contact buyers, file, recommend a buyer, or opine on value** →
  refuse; route to the human approver or the relevant specialist.

## Adjacent-skill handoffs
See [references/handoffs.md](references/handoffs.md). This skill emits a durable `list_id`, a
cited source index, tiered outreach waves, and a conflicts-hold list. Conflicts clearance,
process execution, delivery, and pitch assembly are separate control activities with distinct
owners; the list builder must not perform them.

## Inputs and prerequisites
- A buyer-universe intake: the mandate header (`mandate_id`, process type, masked target, as-of
  date, deal-size band), `freshness_window_days`, the `restricted_list[]`, an `existing_list[]`
  of prior outreach entries, the `sources[]` document index, `candidates[]` (each with
  buyer type, fit inputs, relationship, conflict/restricted flags, and cited `rationale[]`), and
  the `approvals[]` ledger. Schema and checks:
  [scripts/validate_input.py](scripts/validate_input.py).
- Read access to market/financial data, filings, research corpus, document intelligence, CRM,
  and the firm restricted/conflicts list. Drafting is to a controlled workspace only — no
  external send and no buyer contact.

## Source hierarchy
See [references/source-map.md](references/source-map.md). Every fit-rationale and relationship
claim **must cite a document in the source index** (data room, filings, market data, research,
CRM). The restricted/conflicts list is a **versioned contract** used only to flag holds; it
never clears anyone. Conflicting signals are surfaced, not silently resolved.

## Workflow
1. **Validate & index** — run `validate_input`; confirm every source doc has an id, type, and
   `index_ref`; flag candidates missing scoring fields (→ needs-data) and rationale claims whose
   `source_doc` is not in the index (→ unsupported, excluded).
2. **Bind rationale to sources** — for each candidate, bind each rationale claim to a citation;
   drop unsupported claims. A candidate with no supported claim is `needs-source` (excluded).
3. **Screen restricted / conflicts** — flag any candidate on the restricted list or with an
   unresolved conflict as `hold-conflicts-review`; it is excluded from every active wave and
   routed to conflicts clearance, regardless of fit.
4. **Score & tier (deterministic)** — run
   [scripts/calculate_or_transform.py](scripts/calculate_or_transform.py): computes the
   documented fit score, assigns the outreach wave, links duplicates to the prior outreach list,
   and assembles the `list_id`, source index, waves, holds, and gaps.
5. **Draft the deliverable** — populate [assets/output-template.md](assets/output-template.md);
   record approvals as *pending* until humans sign off. Draft only — never send, share, or
   contact.

## Validation loop
Run `validate_input` before and [scripts/validate_output.py](scripts/validate_output.py) after.
The output check enforces: all required template sections present; **no unsupported claims**
(every listed candidate has ≥1 rationale item, each citing a doc in the source index); fit-score
→ wave tie-out; **restricted/conflict candidates never in a wave**; required approvals recorded
(deal_lead + conflicts_reviewer); no send/deliver/outreach-execution language; no
recommendation/valuation-opinion/advice language; standing note present. Fail closed on any miss.

## Human approval
`external-delivery`. The list is an **internal draft**. A `deal_lead` and an independent
`conflicts_reviewer` must be recorded in the approvals ledger, and both must be `approved` before
the list is marked ready for external delivery — and the actual delivery and any buyer outreach
are performed by a human, never by this skill. Internal analytical use may be reviewer-sampled.

## Failure handling
- **Missing scoring field** → `needs-data`; list what is missing; never guess to place a
  candidate.
- **Unsupported / unsourced rationale** → drop the claim; if none remain, `needs-source`
  (excluded); never fabricate or infer a citation.
- **Restricted / conflict** → `hold-conflicts-review`, excluded from waves; route to conflicts
  clearance; do not adjudicate the conflict here.
- **Duplicate of prior outreach** → link to the prior entry for human confirmation; do not
  re-list or auto-merge.
- **Stale source (past freshness window)** → flag; require a refreshed source before placing.
- **Tool timeout** → return the partial list with an explicit `incomplete` flag; no retry
  assumption, no silent completion.

## Output contract
1. **Buyer list draft** — the sections in [assets/output-template.md](assets/output-template.md):
   cover, executive summary, fit criteria, source index, buyer list (cited), outreach waves,
   conflicts hold, gaps, approvals, standing note.
2. **Machine-readable list** — the structured JSON from `calculate_or_transform` keyed by
   `list_id` (source index, buyer list, waves, holds, gaps, summary).
3. **Gaps** — needs-data, needs-source, duplicates, and the excluded unsupported claims.
4. **Standing note** — "Draft buyer/investor list for internal review only; not approved for
   external delivery; no buyer has been contacted and no investment recommendation is made."
See [references/controls.md](references/controls.md).

## Privacy and records
**Highly Confidential — MNPI / client-confidential.** Treat the mandate, target, and buyer
universe as material non-public information: mask target/candidate identifiers to what the list
requires, apply information-barrier and need-to-know controls, and never route content outside
the deal team. Retain the list, source index, citations, restricted-list version, and approval
ledger per the engagement's records policy; log every read, draft, and approval with the analyst
identity.

## Gotchas
- **A wave is a plan, not an action.** Placing a candidate in Wave 1 sequences outreach for a
  human; the skill never contacts anyone.
- **Fit is not a decision.** Scoring and citing a candidate is packaging; whether to approach or
  sell to them is the deal team's judgment, not the skill's.
- **No claim without a resolvable source.** A rationale citing a document missing from the index
  is an unsupported claim and is excluded, not "cited to the data room".
- **Restricted means held, not ranked.** A restricted or conflicted candidate is held for
  clearance and kept out of every active wave — even a perfect-fit one.
- **Draft never ships.** The skill cannot send, share, email, or contact — external delivery and
  outreach are human actions gated on recorded approvals.
- **Handoffs must be real.** Route holds to `conflicts-of-interest-reviewer` and approved lists
  to `transaction-process-tracker` / `investment-banking-pitch-builder`; never invent a skill.
