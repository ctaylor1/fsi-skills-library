---
name: procurement-sourcing-assistant
description: >-
  Assemble procurement sourcing inputs — requirements, supplier market scans, weighted
  evaluation criteria, RFP content, bidder comparisons, third-party risk inputs, and an
  award-recommendation decision record — into ONE source-linked sourcing pack (a draft
  deliverable) for stakeholder review. Use when a sourcing lead, category manager, or business
  sponsor asks to prepare requirements, organize a market scan, build weighted evaluation
  criteria, draft RFP/RFI content, compare bidders on a scorecard, or produce a cited
  award-recommendation for committee review. HARD BOUNDARY: draft-only — never awards a
  contract, selects a winning bidder, or makes a binding sourcing decision; never issues,
  sends, or distributes an RFP or notifies bidders; never negotiates, signs, or commits
  spend; never makes the third-party/cyber/AI vendor-risk or legal determinations (it routes
  them); never fabricates requirements, scores, or approvals. It ranks, recommends, and flags
  open items; humans review, approve, and decide.
license: MIT
compatibility: Amazon Quick Desktop; requires procurement/sourcing (S2P), document-intelligence, contracts/CLM, CRM/supplier-master, knowledge-base, email/calendar, and project-tracking MCP integrations (all read-only).
metadata:
  aws-fsi-category: "Enterprise Functions & Technology"
  aws-fsi-skill-type: "Artifact-creation skills"
  aws-fsi-risk-tier: "R2"
  aws-fsi-archetype: "Draft & package"
  aws-fsi-agent-pattern: "Interactive production copilot"
  aws-fsi-delivery-wave: "Wave 2 - analytical production"
  aws-fsi-action-mode: "Draft-only; no system-of-record change"
  aws-fsi-scheduled-agent: "no"
  aws-fsi-baseline-status: "new"
  aws-fsi-human-approval: "external-delivery"
  aws-fsi-data-classification: "Confidential"
  aws-fsi-jurisdictions: "US (default); configure additional jurisdiction packs per deployment"
  aws-fsi-owner: "Enterprise Functions & Technology"
  aws-fsi-primary-user: "Procurement / business sponsor / technology"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-07-17"
---

# Procurement Sourcing Assistant

## Purpose and outcome
Turn scattered sourcing inputs — stakeholder requirements, a supplier market scan, weighted
evaluation criteria, RFP/RFI content, and bidder responses — into ONE **source-linked
sourcing pack draft** that a human can review and route to an award decision. For each
required section the skill captures the inputs with citations, runs a **deterministic weighted
scorecard** over bidder responses, flags mandatory (knockout) requirements that appear unmet
and bidders with incomplete scoring, routes vendor-risk items to the right specialist skills,
captures recorded approvals plus outstanding required approvals, and compiles an explicit
open-items list. The outcome is a rendered pack from
[assets/output-template.md](assets/output-template.md) plus a machine-readable manifest, with
a **draft award-recommendation** (ranked, cited, pending approval). The skill **ranks and
recommends**; it does not award, select, negotiate, or send.

## Use when
- "Prepare the requirements and evaluation criteria for this sourcing / RFP."
- "Organize the market scan of candidate suppliers with sources."
- "Draft the RFP content sections for this category."
- "Compare the bidder responses on a weighted scorecard and rank them."
- "Build the sourcing decision record / award-recommendation pack for the committee."
- "Capture the recorded approvals and list what's still outstanding, with citations."

## Do not use
- **Binding award / supplier selection / sourcing decision** → refuse; route to the sourcing
  lead, category owner, or procurement committee (no catalog skill makes a binding award).
- **Issuing / sending / publishing the RFP or notifying bidders** → refuse; draft-only. A human
  issues via the procurement system.
- **Third-party / supplier risk assessment** → `third-party-risk-assessor`.
- **Vendor cyber / information-security review** → `third-party-cyber-risk-reviewer`.
- **AI-vendor due diligence** (model/data governance of an AI supplier) →
  `third-party-ai-due-diligence-assistant`.
- **Contract obligation / clause extraction** from an executed or draft agreement →
  `contract-obligation-extractor`.
- **Committee/board pack assembly** for the final governance forum →
  `board-committee-pack-builder`.
- **Contract negotiation, redlining, signature, or PO issuance** → legal / procurement
  operations (human, licensed).

## Adjacent-skill handoffs
See [references/handoffs.md](references/handoffs.md). Sourcing-pack assembly is deliberately
separated from vendor-risk determination, contract work, and the award decision (distinct
controls, entitlements, and accountability). This skill emits a durable `sourcing_id` +
assembled manifest and routes risk items to `third-party-risk-assessor`,
`third-party-cyber-risk-reviewer`, and `third-party-ai-due-diligence-assistant`; it must not
perform those specialists', legal's, or the committee's work.

## Inputs and prerequisites
- The intake bundle: `sourcing_id`, `category`, `jurisdiction`, `as_of_date`,
  `required_sections`, `required_approvals`, the `sponsor`, the `requirements` (each with
  `req_id`, text, priority, owner, `source_ref`), the `market_scan` suppliers, the weighted
  `evaluation_criteria` (each with `criterion_id`, `weight`, `mandatory`), the `rfp_content`
  sections, the `bidders` (each with per-criterion `scores`, `mandatory_met`, `risk_flags`,
  `response_ref`), recorded `approvals`, and any explicit `risk_inputs`. Schema and required
  fields: [scripts/validate_input.py](scripts/validate_input.py).
- Read access to the procurement/sourcing, document-intelligence, CRM/supplier-master,
  contracts/CLM, and knowledge-base sources (all read-only). No input is fabricated: what is
  not supplied becomes an open item or a `needs-data` flag.

## Source hierarchy
See [references/source-map.md](references/source-map.md). The procurement/sourcing system is the
system of record for the sourcing event, bidder responses, and recorded approvals; document
intelligence provides requirement/response documents and citations; the category playbook
defines the required sections, evaluation weights, and required approvals. Cite every asserted
item as `{system}:{ref}@{date/version}`. `required_sections`, `evaluation_criteria` weights,
`required_approvals`, and the pack template are **versioned contracts**.

## Workflow
1. **Validate & normalize** — run `validate_input`; confirm intake structure and surface data
   gaps (unscored criteria, missing requirement owners, weights not summing to 100, missing
   response evidence) as warnings that will become `needs-data` flags or open items.
2. **Assemble & score (deterministic)** — run
   [scripts/calculate_or_transform.py](scripts/calculate_or_transform.py): capture requirements,
   market scan, criteria, and RFP content with citations; compute each bidder's **weighted
   score** from the criteria weights and per-criterion scores; set a bidder status
   (`scored` | `knockout-flag` | `needs-data`); route vendor-risk items; capture recorded and
   outstanding approvals; build the cited source index. Rules:
   [references/domain-rules.md](references/domain-rules.md).
3. **Rank & recommend (draft)** — among fully `scored` bidders that meet mandatory criteria,
   rank by weighted score and mark the top as `recommended-pending-approval`. This is a **draft
   recommendation**, never an award. Ties and knockout/`needs-data` exclusions are stated.
4. **Render the pack** — populate [assets/output-template.md](assets/output-template.md) from the
   manifest; every asserted item (requirement, supplier, bidder score, RFP section, risk input)
   carries its citation.
5. **Compile open items** — everything not complete (unscored criteria, mandatory-unmet
   bidders, missing owners, outstanding approvals, outstanding risk reviews) becomes an explicit
   open item with a required human action. Do not silently drop or infer.
6. **Mark draft & hand off** — set `pack_status: draft-assembled`,
   `award_decision: pending-human-approval`, record that human approval is required before
   delivery, and route risk items to the named specialist skills. Never award, select, send, or
   negotiate.

## Validation loop
Run `validate_input` before and [scripts/validate_output.py](scripts/validate_output.py) after.
The output check enforces: all required template sections present; every asserted
(captured/identified/scored/knockout-flag/drafted/routed) item carries a citation (no
unsupported/unapproved claims); each bidder's stated `weighted_score` ties out to the criteria
weights and scores; recorded approvals carry role, date, and citation and delivery approval is
flagged required; no award/selection, RFP-issuance/send, or negotiation/commitment language;
`pack_status` is `draft-assembled` and `award_decision` is `pending-human-approval`; standing
note present. Fail closed on any miss.

## Human approval
`external-delivery`. This skill produces a **draft** sourcing pack for internal review. A human
must review and approve before the pack is delivered, relied on for an award decision, or
treated as a system-of-record change. The award/supplier-selection decision, RFP issuance,
vendor-risk determinations, and contract execution are separate, human-owned steps — this skill
neither performs nor pre-empts them.

## Failure handling
- **Unscored criterion for a bidder** → bidder status `needs-data`; excluded from the ranking;
  listed as an `unscored-criterion` open item. Never guess a score.
- **Mandatory (knockout) requirement appears unmet** → bidder status `knockout-flag`; excluded
  from the recommendation but still shown and cited; a human confirms elimination.
- **Missing requirement owner / missing response evidence** → captured but flagged as an open
  item; never fabricated.
- **Missing recorded approval** → captured as an outstanding required approval + open item;
  never assumed granted.
- **Vendor-risk flag present** → routed to the specialist skill as an outstanding risk review;
  not adjudicated here.
- **Unresolvable data / tool timeout** → return the partial pack with an explicit incomplete
  flag and the open-items list; no retry assumption, no guessing.

## Output contract
See [references/controls.md](references/controls.md) and
[assets/output-template.md](assets/output-template.md).
1. **Rendered pack** — the template sections (pack summary, requirements, market scan,
   evaluation criteria, RFP content, bidder comparison, risk inputs, decision record, source
   index) populated with cited content.
2. **Machine-readable manifest** — `sourcing_id`, per-section entries with status + citation,
   the weighted scorecard, the draft `recommended-pending-approval` bidder, approvals
   (recorded/outstanding), risk-routing, open items, source index, `pack_status`
   (`draft-assembled`), `award_decision` (`pending-human-approval`), and
   `human_approval_required_before_delivery: true`.
3. **Open-items list** — every unscored/knockout/missing-owner/outstanding item with a required
   human action and (where evidence exists) its citation.
4. **Standing note** — "Draft sourcing pack for human review only. This pack ranks bidders and
   recommends a preferred option for approval; it makes no sourcing decision, creates no
   purchasing commitment, and has not been issued, sent, or negotiated. Any award, delivery, or
   negotiation is a separate, human-approved step."

## Privacy and records
**Confidential.** Bidder responses, pricing, and supplier commercials are competitively
sensitive — restrict to the sourcing team and named approvers; do not disclose one bidder's
response to another. Mask supplier/sponsor identifiers to what the pack requires. Retain the
pack manifest, citations, and config/template versions per the enterprise procurement
recordkeeping policy. Log every read and every pack assembly with the analyst identity. Keep
data within the deployment's residency boundary.

## Gotchas
- **Assembly ≠ award.** Ranking and recommending is not selecting or awarding. The award and
  supplier selection are the committee's / sourcing lead's decision, recorded via the approval
  broker — never state or imply "winning bidder" or a final selection.
- **Draft ≠ issued.** Drafting RFP content is not issuing the RFP. Issuance, sending to
  bidders, and bidder notification are human, system-of-record actions this skill never performs.
- **Scores are cited, never invented.** A missing per-criterion score is `needs-data`, not a
  guessed number; the bidder is excluded from the ranking until scored.
- **Knockout is a flag, not an elimination.** A mandatory requirement that appears unmet is
  surfaced for a human to confirm; the skill does not autonomously disqualify a bidder.
- **Risk is routed, not ruled.** Third-party, cyber, and AI-vendor risk are determinations for
  the specialist skills and their owners; this skill only flags and routes them.
- **Weights are a versioned contract.** Record `evaluation_criteria` weights, `required_sections`,
  `required_approvals`, and the template version on the manifest so the scorecard is reproducible
  and reviewable; weights that do not sum to 100 are flagged.
