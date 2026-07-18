---
name: investment-banking-pitch-builder
description: >-
  Assemble a banker-reviewed investment-banking pitch-book draft from already-approved
  analyses, models, comps, company profiles, market research, client/CRM context, and a
  versioned pitch template. Order pages by the template's required sections, attach a
  one-line takeaway and cited approved sources to every page, map each claim to an approved
  source, check section completeness, run presentation QA, and record the required banker,
  control-room/compliance, and legal/disclaimer approvals. Use when a coverage banker or IB
  analyst asks to build, assemble, or package a pitch book, management presentation, or
  client discussion materials from existing approved components, or to source-map and QA a
  draft deck. DRAFT-ONLY: never sends, submits, distributes, emails, or files materials,
  never fabricates a figure or source, never includes an unsupported or unapproved claim,
  and never gives personalized investment advice - external delivery requires the recorded
  human approvals and is performed by a person, not this skill.
license: MIT
compatibility: Amazon Quick Desktop; requires controlled-template-library, approved-analysis/model artifact store, market-data, filings, research-corpus, CRM, and data-room MCP integrations (all read-only); no send/deliver capability is bound.
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
  aws-fsi-primary-user: "Coverage banker / investment-banking analyst"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-07-17"
---

# Investment Banking Pitch Builder

## Purpose and outcome
Assemble a **draft** pitch book from components that were already produced and approved
elsewhere - comps, DCF and other models, company profiles, market pages, buyer lists, and
client context - against a **versioned pitch template**. The skill orders pages by the
template's required sections, attaches a one-line takeaway and cited approved sources to
each page, maps every claim to an approved source, runs completeness and presentation QA,
and records the required approvals. The outcome is a source-mapped, QA'd pitch-book draft
that a banker can review and that a person can deliver **after** the recorded sign-offs -
not a delivered deck, and not newly-originated analysis.

## Use when
- "Assemble / build / put together a pitch book (or management presentation, discussion
  materials) for `{client}` from the approved comps, DCF, and market pages."
- "Source-map and QA this draft deck before the banker review."
- "Check the pitch is complete against our template and that every page is sourced."
- "Roll up the approvals and tell me what's blocking delivery."

## Do not use
- **Building the analyses/models** (comps, DCF, three-statement, merger/LBO, scenarios,
  profiles, market sizing) -> the upstream IB skills (see Adjacent-skill handoffs).
- **Sending, emailing, distributing, or filing** the deck -> refuse; delivery is a human
  action after approvals.
- **Conflicts / control-room adjudication** or the **communications-compliance review** ->
  `conflicts-of-interest-reviewer`, `communications-compliance-reviewer`.
- **Personalized investment/legal/tax advice**, guaranteed-return or promissory language ->
  refuse.

## Adjacent-skill handoffs
See [references/handoffs.md](references/handoffs.md). Content construction is **upstream**
(comps/DCF/models/profiles/market pages); this skill only **assembles and packages** and
never delivers. Control clearance (`conflicts-of-interest-reviewer`,
`communications-compliance-reviewer`) and MD/legal sign-off are separate; external delivery
is a human action. A stale or unsourced page is routed back to its upstream skill, not
edited in place.

## Inputs and prerequisites
- A **pitch build request**: `engagement_id`; the `template` (`template_id`, `version`,
  `required_sections`); `deal_context` (client, mandate, audience, classification);
  `required_approvals`; recorded `approvals`; and `pages` - each with a section, title,
  `source_component`, takeaway, `claims[{text, source_ref, approved}]`, `sources[]`, and a
  content `approval`. Schema: [scripts/validate_input.py](scripts/validate_input.py).
- Read access to the template library, the approved-artifact store, market data, filings,
  CRM, and (where engaged) the data room. No delivery capability.

## Source hierarchy
See [references/source-map.md](references/source-map.md). The **template** is the top
versioned contract; then approved analysis/model artifacts, filings/market data, research
corpus, CRM, and the data room. The skill never originates figures - it cites the upstream
component. Every page carries at least one source; every claim carries a `source_ref`.

## Workflow
1. **Validate the request** - run [scripts/validate_input.py](scripts/validate_input.py):
   confirm the template contract and pages exist; warn on completeness, source, and approval
   gaps that will force `hold-for-approval`.
2. **Assemble the draft (deterministic)** - run
   [scripts/calculate_or_transform.py](scripts/calculate_or_transform.py): order pages by
   the template's required sections, compute a per-page status (`ready` / `needs-source` /
   `unsupported-claim` / `needs-approval`), map each claim to its approved source, and list
   any unsupported claims and missing sections.
3. **Roll up approvals & set delivery status** - record `banker_signoff`,
   `compliance_control_room`, and `legal_disclaimers`; set `approved-for-delivery` **only**
   when all sections present, all pages `ready`, and all required approvals `approved`;
   otherwise `hold-for-approval`.
4. **Presentation QA** - fill [assets/output-template.md](assets/output-template.md); flag
   blocked pages and unsupported claims for the banker; route gaps upstream.
5. **Never deliver** - the draft is handed to a person; this skill does not send/submit/file.

## Validation loop
Run `validate_input` before and [scripts/validate_output.py](scripts/validate_output.py)
after. The output check enforces: every required template section present; every page has a
takeaway and a cited source; every claim has an approved `source_ref`; no promissory/
guarantee/advice language; each required approval recorded (and `approved-for-delivery` only
if all approved); the delivery status is never a delivered state; the draft-only notice and
standing note are present. Fail closed on any miss.

## Human approval
`external-delivery`. The skill drafts and QAs; it does not approve or deliver. A deal-captain
MD sign-off, control-room/compliance clearance (MNPI, conflicts, wall-cross), and
legal/disclaimer review must be **recorded** before the draft is `approved-for-delivery`,
and a person performs the actual delivery. The preparer must not self-approve the required
control approvals (segregation of duties).

## Failure handling
- **Missing / unsourced figure** -> mark the page `needs-source`; route to the upstream
  skill. Never back-fill a "reasonable" number.
- **Unapproved claim** -> mark `unsupported-claim`; page cannot be `ready`.
- **Missing required section** -> stays `hold-for-approval`; list the gap.
- **Stale template/version or data** -> flag; re-pull from the source, do not edit in place.
- **Missing approval** -> `hold-for-approval`; name the unrecorded role.
- **Tool timeout / partial inputs** -> return the partial draft with an explicit incomplete
  flag; no retry assumption; never mark deliverable.

## Output contract
1. **Assembled draft** - `engagement_id`, `template_id@version`, ordered `pages` (each with
   status, takeaway, sources, claims), `sections_present`/`sections_missing`.
2. **Approvals roll-up** - `required_approvals`, recorded `approvals` + status, and
   `delivery_status` (`draft` | `hold-for-approval` | `approved-for-delivery`).
3. **Unsupported / blocked items** - pages not `ready` and claims lacking an approved source.
4. **Machine-readable** - the full draft JSON keyed by `engagement_id`.
5. **Draft-only notice + standing note** - "Draft pitch materials only; no materials have
   been sent, delivered, distributed, or filed..."
See [references/controls.md](references/controls.md) and
[references/domain-rules.md](references/domain-rules.md).

## Privacy and records
**Highly Confidential (MNPI / client-confidential).** Information-barrier / wall-cross and
control-room clearance apply; no selective disclosure; distribution to cleared recipients
only, by a person. Retain the draft, its source map, the template `id@version`, and the
approval records per records policy; log preparer identity and every approval.

## Gotchas
- **Assemble, don't originate.** Every number comes from an approved upstream component with
  a `source_ref`; if it isn't sourced, it isn't a claim you can keep - route it upstream.
- **Approved-for-delivery is not delivery.** It means humans cleared the draft; a person
  still delivers. This skill never sends.
- **Template is a versioned contract.** Record `template_id@version`; a superseded version
  or a missing required section blocks delivery.
- **Promissory language is prohibited even if "sourced."** Guarantee/risk-free/will-outperform
  language never belongs in pitch materials.
- **Segregation of duties.** The preparer does not self-approve control-room or legal
  sign-off.
