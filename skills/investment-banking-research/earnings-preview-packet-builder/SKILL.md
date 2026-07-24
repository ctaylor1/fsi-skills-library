---
name: earnings-preview-packet-builder
description: >-
  Compile a source-backed, pre-event earnings preview packet for an equity/credit research
  associate: reporting/call calendar, third-party consensus, prior guidance (as issued),
  historical KPIs with QoQ/YoY trends, known controversies, disclosed sensitivities,
  attributed bull/bear debate points, and open questions - assembled against a versioned
  template with every figure cited and every forward-looking number attributed to consensus
  or guidance. Use when a buy- or sell-side research associate asks to build,
  assemble, or compile an earnings preview, pre-event brief, or consensus-vs-guidance snapshot
  before a company reports. HARD BOUNDARY: never sets a forecast, rating, price target, or
  trade view, never originates an estimate or gives personalized advice, and never publishes
  or distributes; pre-event only (post-event beat/miss and thesis-impact analysis is
  earnings-results-analyzer); distribution requires recorded supervisory-analyst,
  research-compliance, and legal approvals, performed by a person.
license: MIT
compatibility: Amazon Quick Desktop; requires controlled-template-library, issuer-filings, earnings-transcripts, consensus/estimates, market-data, research-corpus/news, and CRM MCP integrations (all read-only); no publish/send/distribute capability is bound.
metadata:
  aws-fsi-category: "Investment Banking & Research"
  aws-fsi-skill-type: "Artifact-creation skills"
  aws-fsi-risk-tier: "R2"
  aws-fsi-archetype: "Draft & package"
  aws-fsi-agent-pattern: "Interactive production copilot"
  aws-fsi-delivery-wave: "Wave 5 - 2026 industry expansion"
  aws-fsi-action-mode: "Draft-only; no system-of-record change"
  aws-fsi-scheduled-agent: "no"
  aws-fsi-baseline-status: "new"
  aws-fsi-human-approval: "external-delivery"
  aws-fsi-data-classification: "Highly Confidential (MNPI / client-confidential)"
  aws-fsi-jurisdictions: "US (default); configure additional jurisdiction packs per deployment"
  aws-fsi-owner: "Investment Banking / Research"
  aws-fsi-primary-user: "Equity/credit research associate"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-07-17"
---

# Earnings Preview Packet Builder

## Purpose and outcome
Compile a **draft**, source-backed pre-event earnings preview packet from already-sourced
components - the reporting calendar, third-party consensus, prior company guidance (as
issued), historical KPIs, known controversies, disclosed sensitivities, attributed bull/bear
debate points, and open questions - against a **versioned template**. The skill orders items
by the template's required sections, attaches a factual "what to watch" takeaway and cited
sources to every item, attributes every forward-looking figure to consensus or company
guidance, computes descriptive consensus-vs-guidance positioning and KPI trends, runs
completeness/QA, and records the required approvals. The outcome is a source-mapped, QA'd
preview brief that a supervisory analyst and compliance can review and that a person can
distribute **after** the recorded sign-offs - not a delivered brief, and not a house view.

## Use when
- "Build / assemble / compile an earnings preview packet for `{ticker}`'s upcoming print."
- "Put together a pre-event brief: reporting date, consensus, prior guidance, historical
  KPIs, controversies, sensitivities, and open questions."
- "Give me the consensus-vs-guidance snapshot and the debate points before earnings."
- "Source-map and QA this preview brief before the supervisory-analyst review."

## Do not use
- **Post-event analysis** - beat/miss vs consensus, guidance revision, transcript changes,
  thesis impact -> `earnings-results-analyzer` (this skill stops at the print).
- **Setting a forecast, rating, price target, or trade view**, originating an estimate, or
  giving personalized investment advice -> refuse (hard boundary).
- **Building full sensitivity/scenario exhibits** -> `scenario-sensitivity-generator`;
  **in-depth controversy investigation** -> `adverse-media-investigator`.
- **Publishing / sending / distributing / filing** the packet -> refuse; distribution is a
  human action after approvals.
- **Conflicts / control-room adjudication** or the **communications-compliance review** ->
  `conflicts-of-interest-reviewer`, `communications-compliance-reviewer`.

## Adjacent-skill handoffs
See [references/handoffs.md](references/handoffs.md). Content sourcing is **upstream** (feeds,
filings, transcripts, profiles, sensitivity/controversy work); this skill only **compiles and
packages**, strictly pre-event, and never delivers. Post-event work belongs to
`earnings-results-analyzer`. Control clearance and legal sign-off are separate; distribution
is a human action. A stale or unsourced item is routed back to its upstream skill, not edited
in place. The packet is keyed by a durable `packet_id` (+ `job_id`).

## Inputs and prerequisites
- A **preview build request**: durable `packet_id` and `job_id`; `as_of_date`; `issuer`
  (name, ticker); `event` (fiscal_period, report_date, comparable_period); the `template`
  (`template_id`, `version`, `required_sections`); `metrics[]` (consensus value + prior
  guidance range per metric, each with a source); `kpi_history[]` (reported series per KPI);
  `required_approvals`; recorded `approvals`; and `items[]` - each with a section, title,
  `source_component`, takeaway, `data_points[{label, value, kind, attribution, source_ref,
  approved}]`, `sources[]`, and a content `approval`. Schema:
  [scripts/validate_input.py](scripts/validate_input.py).
- Read access to the template library, issuer filings, transcripts, consensus/estimates,
  market data, research corpus/news, and CRM. No delivery capability.

## Source hierarchy
See [references/source-map.md](references/source-map.md). The **template** is the top
versioned contract; then issuer filings (guidance as issued, KPIs, disclosed sensitivities,
dates), transcripts, third-party consensus/estimates, market data, research corpus/news, and
CRM. The skill never originates a figure or a view - it cites the source and attributes every
forward-looking number to consensus or company guidance. Every item carries at least one
source; every data point carries a `source_ref` and an `attribution`.

## Workflow
1. **Validate the request** - run [scripts/validate_input.py](scripts/validate_input.py):
   confirm `packet_id`, issuer/event, the template contract, and items exist; warn on
   completeness, source, attribution, and approval gaps that force `hold-for-approval`;
   reject any originated-view data-point kind.
2. **Assemble the packet (deterministic)** - run
   [scripts/calculate_or_transform.py](scripts/calculate_or_transform.py): order items by the
   template's required sections; compute a per-item status (`ready` / `needs-source` /
   `unsupported-claim` / `needs-approval`); map each data point to its approved, attributed
   source; compute **descriptive** consensus-vs-guidance positioning (below/within/above +
   gap to midpoint) and KPI QoQ/YoY trends from reported figures; list unsupported items and
   missing sections. No figure is projected for the upcoming period.
3. **Roll up approvals & set status** - record `supervisory_analyst`, `research_compliance`,
   and `legal_disclaimers`; set `ready-for-distribution` **only** when all sections present,
   all items `ready`, and all required approvals `approved`; otherwise `hold-for-approval`.
4. **QA** - fill [assets/output-template.md](assets/output-template.md); flag blocked items,
   unattributed forward-looking figures, and unsupported data points; route gaps upstream.
5. **Never deliver** - the packet is handed to a person; this skill does not publish/send/file.

## Validation loop
Run `validate_input` before and [scripts/validate_output.py](scripts/validate_output.py)
after. The output check enforces: every required template section present; every item has a
takeaway and a cited source; every data point has an approved `source_ref` and (if
forward-looking) a third-party attribution; **no forecast / rating / price-target /
trade-view / advice language** and no originated-view data-point kind (the R2 prohibited-
decision/advice screen); each required approval recorded (and `ready-for-distribution` only
if all approved); the status is never a distributed state; the draft-only notice and standing
note are present. Fail closed on any miss.

## Human approval
`external-delivery`. The skill compiles and QAs; it does not opine, approve, or distribute. A
supervisory-analyst sign-off, research-compliance / control-room clearance (MNPI, conflicts,
wall-cross), and legal/disclaimer review must be **recorded** before the packet is
`ready-for-distribution`, and a person performs the actual distribution. The preparer must
not self-approve the required control approvals (segregation of duties).

## Failure handling
- **Missing / unsourced figure** -> mark the item `needs-source`; route to the upstream skill.
  Never back-fill a "reasonable" number.
- **Unattributed forward-looking figure** -> `unsupported-claim`; a consensus/guidance/
  sensitivity data point must name its third-party source, never the analyst/house.
- **Request to add a forecast/rating/target/trade view** -> refuse (hard boundary); the
  packet compiles sourced facts and attributed debate points only.
- **Missing required section** -> stays `hold-for-approval`; list the gap.
- **Stale template/version, consensus, or data** -> flag; re-pull from the source, do not
  edit in place. Guidance is quoted as originally issued.
- **Missing approval** -> `hold-for-approval`; name the unrecorded role.
- **Tool timeout / partial inputs** -> return the partial packet with an explicit incomplete
  flag; no retry assumption; never mark distributable.

## Output contract
1. **Assembled packet** - `packet_id`, `job_id`, `as_of_date`, issuer, event; `template_id@
   version`; ordered `items` (each with status, takeaway, sources, attributed data points);
   `sections_present`/`sections_missing`.
2. **Descriptive tables** - `consensus_vs_guidance` (position + gap to midpoint) and
   `kpi_trends` (QoQ/YoY), computed from sourced figures only.
3. **Approvals roll-up** - `required_approvals`, recorded `approvals` + status, and
   `packet_status` (`draft` | `hold-for-approval` | `ready-for-distribution`).
4. **Unsupported / blocked items** - items not `ready`, data points lacking an approved
   source, forward-looking figures lacking an attribution.
5. **Machine-readable** - the full packet JSON keyed by `packet_id`.
6. **Draft-only notice + standing note** - "Pre-event preview compilation only; no forecast,
   price target, rating, or trade view has been set, and no packet has been published or
   distributed..."
See [references/controls.md](references/controls.md) and
[references/domain-rules.md](references/domain-rules.md).

## Privacy and records
**Highly Confidential (MNPI / client-confidential).** Information-barrier / wall-cross and
control-room clearance apply; no selective disclosure; distribution to cleared recipients
only, by a person. Retain the packet, its source map, the template `id@version`, the
`packet_id`/`job_id`, and the approval records per the research records-retention policy; log
preparer identity and every approval.

## Gotchas
- **Compile, don't opine.** Every number comes from a source with a `source_ref`; every
  forward-looking figure is attributed to consensus or company guidance. If it isn't sourced
  and attributed, it isn't a data point you can keep - route it upstream.
- **Consensus is not your estimate.** Consensus is a cited third-party aggregate; guidance is
  reproduced as issued. The consensus-vs-guidance positioning and KPI deltas are descriptive
  arithmetic on sourced numbers, never a forecast of the print.
- **Pre-event only.** The moment the discussion is about the reported result, hand off to
  `earnings-results-analyzer`.
- **Ready-for-distribution is not distribution.** It means humans cleared the packet; a person
  still distributes. This skill never publishes or sends.
- **Segregation of duties.** The preparer does not self-approve supervisory-analyst,
  compliance, or legal sign-off.
