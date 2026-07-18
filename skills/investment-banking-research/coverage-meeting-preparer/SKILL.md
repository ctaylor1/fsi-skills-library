---
name: coverage-meeting-preparer
description: >-
  Prepare a client or prospect coverage-meeting brief from approved sources: relationship
  history, recent company and market developments, strategic issues, the counterparty's
  likely objectives, discussion questions, and follow-ups — a fully source-cited DRAFT from
  an approved template. Use when a coverage banker or relationship manager needs
  to prep for a client or prospect meeting, build a pre-read or briefing pack, or pull
  together background, strategic angles, and talking points ahead of a coverage call.
  Keywords: coverage meeting, client brief, prospect brief, relationship history, briefing
  pack, talking points, discussion questions, follow-ups. NEVER sends, distributes, files,
  or executes anything; makes no investment recommendation, price target, or valuation
  opinion; gives no investment, legal, or tax advice; keeps any MNPI private-side and
  internal-only; and states nothing not backed by a cited approved source — it drafts for
  supervisory and control-room review; external delivery is a human action.
license: MIT
compatibility: Amazon Quick Desktop; requires market/financial-data, filings, research-corpus, CRM, and data-room MCP integrations (all read-only; drafting only — no send, file, or distribute).
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
  aws-fsi-primary-user: "Coverage banker / senior relationship manager"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-07-17"
---

# Coverage Meeting Preparer

## Purpose and outcome
Turn an upcoming client or prospect meeting and its approved context into an audit-ready
**coverage-meeting brief (pre-read)**: relationship history, recent company and market
developments, the strategic issues in play, the counterparty's likely objectives, discussion
questions, and follow-ups — assembled as a concise, **fully source-cited DRAFT** from an
approved template. The outcome is a review-ready briefing pack (or a clear, itemized reason
it cannot be assembled yet) that a coverage banker verifies, a supervisor and — where MNPI is
present — the control room clear, and that a human (not this skill) delivers. The brief states
nothing a cited approved source does not support, issues no recommendation, and never sends or
files anything.

## Use when
- "Prep me for the Northwind meeting on Thursday — pull relationship history, recent
  developments, and what they're likely to want."
- "Build a pre-read / briefing pack for the prospect intro with the strategic issues and
  discussion questions."
- "Pull the background, open items, and talking points going into this coverage call."
- "What follow-ups and questions should I take into the client review?"

## Do not use
- **Full company profile / business overview** assembly → `company-profile-builder`.
- **Deep earnings analysis** of the latest results → `earnings-results-analyzer`.
- **Sector / competitive landscape research** → `market-landscape-researcher`.
- **Trading-multiple / comps work** → `comps-analysis-builder`; **valuation modeling** →
  `dcf-modeler` (this brief cites outputs as facts; it never recomputes or opines on value).
- **Turning the brief into a client-facing pitch book** → `investment-banking-pitch-builder`.
- **Data-room diligence pack** → `due-diligence-packager`.
- Any request to **send/distribute/file, decide, commit, recommend, price, or advise** →
  refuse; draft only and route to a human. See [references/handoffs.md](references/handoffs.md).

## Adjacent-skill handoffs
See [references/handoffs.md](references/handoffs.md). This skill is **prep-time drafting
only**. It consumes read-only, sourced context (profile facts, earnings analysis, sector
context, comps, CRM history, filings, and — private-side — data-room material) and emits an
`engagement_id`-keyed DRAFT brief with `reviewer_signoff_required` and a recorded-approvals
block. Profiling, earnings/sector/comps analysis, pitch assembly, diligence packaging, live
mandate/pricing decisions, MNPI wall-crossing, and any external delivery belong to the routes
above or to an authorized human.

## Inputs and prerequisites
- The intake record per meeting: `engagement_id`, `client_name`, `meeting_type`
  (`client` | `prospect`), `meeting_date`, `objective`, preparer; a **source inventory**
  (`sources[]` with `source_id`, `system`, `ref`, `date`, optional `classification`); the
  `relationship` block (coverage since, last meeting, mandates, open items); and the content
  lists `developments`, `strategic_issues`, `client_objectives`, `discussion_questions`,
  `follow_ups`. Every content item cites a `source_id` in the inventory. Schema:
  [scripts/validate_input.py](scripts/validate_input.py).
- An `as_of_date` (drives freshness) and a `freshness_days` threshold; the approved source
  systems list; the `approvals` block (supervisory review, control-room clearance, external
  delivery). Rules and thresholds: [references/domain-rules.md](references/domain-rules.md).
- Read access to market/financial-data, filings, research corpus, CRM, and the data room. No
  write, send, or file capability is used.

## Source hierarchy
See [references/source-map.md](references/source-map.md). CRM is the system of record for the
relationship and interactions; filings/transcripts and market data supply company facts;
research supplies sector context; the data room supplies **private-side / MNPI** material.
**Cite every item** with `{system}:{ref}@{date}`. Nothing enters the brief without a source;
the approved brief template and the approved-source list are **versioned contracts**.

## Workflow
1. **Validate & normalize** — run `validate_input`; confirm each meeting is structurally
   complete and every content item cites a source in the inventory; flag gaps as warnings.
2. **Assemble deterministically** — run
   [scripts/calculate_or_transform.py](scripts/calculate_or_transform.py): deduplicate and
   date-sort developments, bind every claim to an approved in-inventory source, screen source
   freshness against `freshness_days`, and tag any MNPI claim private-side / internal-only.
3. **Assign status (precedence)** — `needs-data` → `unsupported-claims` → `stale-source` →
   `barrier-hold` (MNPI present without recorded control-room clearance) each block assembly
   with an itemized reason; only a clean, cleared record becomes `draft-brief`.
4. **Draft the brief** — for a packageable meeting, assemble the brief from
   [assets/output-template.md](assets/output-template.md): meeting snapshot, relationship
   history, developments, strategic issues, likely objectives, discussion questions,
   follow-ups, a citations index, the handling label, and the required-approvals block. No
   statement without a cited source; MNPI stays in internal-only fields.
5. **Validate output** — run [scripts/validate_output.py](scripts/validate_output.py); fail
   closed on any miss (template fidelity, unsupported/unapproved claims, blocking stale
   sources, MNPI-in-shareable-field, missing approvals, delivery/advice language, standing
   note).
6. **Never deliver** — hand the reviewed DRAFT to the banker; supervisory review and
   control-room clearance are recorded; a human delivers externally.

## Validation loop
Run `validate_input` before and `validate_output` after. The output screen enforces: template
fidelity (required sections, no unfilled `{{placeholder}}` tokens); a packageable record is
fully source-cited (no unsupported/unapproved claim), free of blocking stale sources, with
every MNPI claim internal-only; supervisory review approved and — if MNPI is present —
control-room clearance approved; an external-delivery slot recorded but never marked
sent/delivered; no send/distribute/file/execute language and no recommendation/price-target/
valuation-opinion/advice language; standing note present. See
[references/controls.md](references/controls.md). Correct and re-run until it passes or the
record is flagged not-packageable.

## Human approval
`external-delivery`. A human must review and authorize before the brief is delivered or any
system of record (CRM, data room) is changed; where MNPI is present, control-room clearance is
required before the draft is relied on. This skill proposes and drafts; it never sends,
decides, commits, recommends, prices, or advises. Internal drafting may be reviewer-sampled
per [references/controls.md](references/controls.md).

## Failure handling
- **Missing required input** (no objective, developments, client objectives, or discussion
  questions) → `needs-data`; list exactly what is missing; do not invent an agenda, a fact, or
  an objective.
- **Claim cites an unknown/unapproved source** → `unsupported-claims`; drop or substantiate
  the item; never fabricate a development, figure, or quote to fill the brief.
- **Stale source** (older than `freshness_days`, not acknowledged) → `stale-source`; refresh or
  explicitly acknowledge it; never present stale context as current.
- **MNPI present without recorded control-room clearance** → `barrier-hold`; route to the
  control room; never place MNPI in a shareable field or externalize it.
- **Ambiguous client identity** → leave `unresolved` for a human; never auto-merge accounts.
- **Tool timeout / partial context** → return partial output with an explicit incomplete flag
  and the sources used; no retry assumption.

## Output contract
1. **Prep queue** — per meeting: `engagement_id`, `client_name`, `meeting_type`, status,
   `packageable`, and a one-line reason.
2. **Coverage-meeting brief** (per packageable meeting) — meeting snapshot, relationship
   history, developments (deduped, date-sorted), strategic issues, likely objectives,
   discussion questions, follow-ups, a citations index, the handling label, the
   required-approvals block, and `reviewer_signoff_required: true`, following
   [assets/output-template.md](assets/output-template.md).
3. **Blocked list** — each non-packageable meeting with its itemized reason(s).
4. **Machine-readable** — the brief records keyed by `engagement_id` with `as_of_date`,
   `config_version`, and the approved-source list.
5. **Standing note** — "Draft coverage-meeting brief for internal preparation only; this skill
   does not send, distribute, file, or execute anything, makes no investment recommendation,
   price target, or valuation opinion, and states nothing not backed by a cited approved
   source. Any material non-public information is tagged private-side and internal-only;
   external delivery requires the recorded control-room and delivery approvals."

## Privacy and records
**Highly Confidential (MNPI / client-confidential).** Information-barrier discipline applies:
private-side / MNPI material is tagged internal-only and never placed in a shareable field or
externalized without recorded control-room clearance. Data minimization — include only the
context needed to prepare for the meeting; mask personal identifiers to what the brief
requires. Retain the DRAFT brief, the `as_of_date`, source citations, the config/template
versions, and the approvals with the engagement record; log every read and every brief
produced with the preparer identity. Delivery and any system-of-record change are human
actions outside this skill.

## Gotchas
- **Drafting ≠ delivering.** The brief is a DRAFT pre-read; a human delivers it. Never emit
  "sent / distributed / posted to CRM / filed" language or imply anything was shared.
- **Report, never recommend.** The brief surfaces sourced developments, issues, and the
  counterparty's likely objectives; it never tells the client (or the banker) to buy, sell,
  refinance, or sign, and never states a price target or valuation opinion — that is licensed
  research/advice.
- **Every line needs a source.** A confident sentence with no citation is an unsupported
  assertion and is stripped by the output screen — no development, figure, quote, or objective
  without a `source_id` on the approved list.
- **MNPI stays behind the wall.** Private-side material is internal-only; it never lands in a
  shareable field, and its presence forces recorded control-room clearance before the draft is
  relied on. Mixing MNPI into an externally-shareable brief is an information-barrier breach.
- **Freshness matters.** A months-old note presented as current context misleads the room;
  unacknowledged stale sources block, and the brief records the `as_of_date`.
- **Likely objectives are inferences to test, not facts.** Frame the counterparty's objectives
  as sourced hypotheses to confirm in the room, not as decided outcomes.
