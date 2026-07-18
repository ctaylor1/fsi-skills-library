---
name: company-profile-builder
description: >-
  Assemble a draft company profile or strip page for investment-banking and research use —
  business overview, KPIs and operating/financial metrics, ownership, management, trading
  data, precedent transactions, and a cited source index — mapping every stated fact to an
  approved source. Use when an analyst asks to build or refresh a company profile, a
  one-pager, or a strip page, map facts to profile sections, or flag what is missing or
  unsourced before a banker reviews it. HARD BOUNDARY: draft-only — it never distributes,
  sends, or submits the profile, never issues investment advice, a rating, a recommendation,
  or a price-target opinion, never asserts an unsourced fact, and never includes material
  non-public information (MNPI) in an externally distributed profile. Unsourced facts, stale
  data, identity mismatches, and MNPI become open items for human resolution; external
  delivery and required approvals stay with the banker/compliance via the approval broker.
license: MIT
compatibility: Amazon Quick Desktop; requires market/financial-data, filings/EDGAR, research-corpus, entity-resolution, document-intelligence, CRM, and data-room MCP integrations (all read-only), plus spreadsheet/presentation export.
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
  aws-fsi-primary-user: "Investment-banking analyst"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-07-17"
---

# Company Profile Builder

## Purpose and outcome
Assemble a **draft** company profile / strip page from approved facts: business overview,
KPIs and operating/financial metrics, ownership, management, trading data, precedent
transactions, and a deduplicated **source index**. Every asserted fact is mapped to its
section and carries a citation; anything unsourced, stale, identity-mismatched, or
MNPI-restricted is routed to an **open-items** list instead of being asserted. The outcome
is a review-ready draft plus an explicit gap list — the banker/analyst edits, a supervisory
analyst and compliance approve, and a human distributes. This skill never distributes,
advises, rates, or fabricates.

## Use when
- "Build/refresh the company profile (strip page / one-pager) for {company}."
- "Map these facts — overview, KPIs, ownership, management, trading data, transactions — to
  the profile template."
- "What's missing or unsourced on this profile before it goes to the banker?"
- "Assemble the profile and list the open items and outstanding approvals."

## Do not use
- **Comparable-company / trading-multiple analysis** → `comps-analysis-builder`.
- **Valuation (DCF/LBO/merger/three-statement)** → `dcf-modeler`, `lbo-model-builder`,
  `merger-model-builder`, `three-statement-model-builder`.
- **Post-earnings beat/miss analysis** → `earnings-results-analyzer`.
- **Industry/theme landscape** → `market-landscape-researcher`.
- **Assembling the client-facing deck** from approved analyses →
  `investment-banking-pitch-builder`.
- Any **investment advice, rating, recommendation, or price-target opinion**, any
  **distribution/delivery**, or inclusion of **MNPI in an external profile** → refuse; these
  are human/compliance-owned (see below).

## Adjacent-skill handoffs
See [references/handoffs.md](references/handoffs.md). Profile-building is a distinct control
activity from analysis, modeling, and deck assembly. This skill emits a durable `profile_id`
plus an assembled manifest and open-items list; downstream skills and humans consume that
manifest rather than re-assembling. It never performs the analyst's valuation work or the
banker's distribution.

## Inputs and prerequisites
- Intake bundle: `profile_id`, `company` (id, legal name, ticker, entity type), `as_of_date`,
  `intended_distribution` (`internal` | `external`), `required_sections`, `required_approvals`,
  `facts[]` (each: `section`, `fact_id`, `label`, `value`, `source_ref`, `effective_date`,
  optional `expires`, `mnpi`, `company_id`), and any recorded `approvals[]`. Schema:
  [scripts/validate_input.py](scripts/validate_input.py).
- Read access to market/financial data, filings, research corpus, entity resolution,
  document intelligence, CRM, and the data room. **Read-only.**

## Source hierarchy
See [references/source-map.md](references/source-map.md). Filings are authoritative for
overview/ownership/management/precedent facts; market/financial data is authoritative for
trading data (time-sensitive, as-of dated); the data room supplies deal-confidential facts
(often MNPI). Every asserted fact carries `{system}:{ref}@{date/version}`. Required sections,
required approvals, and the profile template are **versioned contracts**.

## Workflow
1. **Validate & normalize** — run `validate_input`; confirm structure, dedupe `fact_id`s,
   and surface data gaps (unsourced facts, undated facts, MNPI-in-external warnings).
2. **Assemble (deterministic)** — run
   [scripts/calculate_or_transform.py](scripts/calculate_or_transform.py): map each fact to
   its section and assign a status — `included`, `stale` (past `expires` vs `as_of`),
   `unresolved` (company-identity mismatch), `restricted-mnpi` (MNPI in an external profile),
   or `unsupported` (no citation). Only `included`/`stale`/`unresolved` are asserted in the
   profile; `unsupported` and `restricted-mnpi` are **routed to open items, never asserted**.
3. **Capture approvals** — record recorded approvals (role, date, citation) and mark
   required-but-missing approvals as **outstanding** open items.
4. **List open items** — unsourced claims, stale data, identity mismatches, MNPI exclusions,
   incomplete required sections, and outstanding approvals — each with the required human
   action.
5. **Render to template** — populate [assets/output-template.md](assets/output-template.md);
   `assembly_status` stays `draft-assembled`.
6. **Never distribute / advise** — no send/submit, no rating/recommendation/price-target.

## Validation loop
Run `validate_input` before and [scripts/validate_output.py](scripts/validate_output.py)
after. The output check enforces: all required template sections present; **no unsupported
assertions** (every asserted fact carries a citation, no unsourced fact appears in a
section); **no MNPI** in an external profile; required approvals recorded (role/date/citation)
and delivery approval flagged as required; no investment-advice/rating/recommendation or
distribution/delivery language; `assembly_status: draft-assembled`; standing note present.
Fail closed on any miss.

## Human approval
`external-delivery`. Internal analytical drafting is reviewer-sampled; **before any external
distribution or system-of-record change**, a supervisory/research analyst and compliance
(control room) must approve, and a human distributes via the approval broker. This skill
proposes a draft and a gap list — humans decide, approve, and deliver.

## Failure handling
- **Unsourced fact** → `unsupported` open item ("attach an approved source or remove the
  claim"); never asserted, never fabricated to fill a section.
- **Stale trading/market data** → `stale`; keep cited, flag for refresh as of the profile date.
- **Ambiguous / mismatched entity** → `unresolved`; reconcile with a human, never auto-merge.
- **MNPI in an external profile** → excluded and flagged for wall-crossing / compliance
  clearance; never silently included.
- **Incomplete required section** → `section-incomplete` open item; do not pad with
  unsourced content.
- **Tool timeout / partial data** → return the partial draft with an explicit incomplete
  flag; assume no retry.

## Output contract
1. **Profile manifest** — `sections{profile_summary, business_overview, key_financials,
   ownership, management, trading_data, transactions, sources}`; each asserted entry carries
   `status` + `citation`.
2. **Open-items list** — every gap (unsourced, stale, unresolved, MNPI-excluded,
   section-incomplete, outstanding-approval) with the required human action.
3. **Approvals** — recorded (role/date/citation) and outstanding.
4. **Source index** — deduplicated citations backing every asserted fact.
5. **Machine-readable** — the manifest keyed by `profile_id`; `assembly_status:
   draft-assembled`, `human_approval_required_before_delivery: true`.
6. **Standing note** — "Draft company profile for human review only. This profile is not
   investment advice or a recommendation, every stated fact is source-cited, and the profile
   has not been distributed or delivered."
See [references/controls.md](references/controls.md) and
[references/domain-rules.md](references/domain-rules.md).

## Privacy and records
**Highly Confidential (MNPI / client-confidential).** Treat the profile and its deal context
as confidential; mask internal company identifiers to what the profile needs. Enforce
information-barrier controls: MNPI never enters an external profile without documented
wall-crossing/compliance clearance. Retain the manifest, open items, approvals, and citations
with the template/config versions; log every read and assembly with the analyst identity.

## Gotchas
- **Assembly ≠ approval ≠ distribution.** A `draft-assembled` profile is not cleared,
  approved, or sent; those are separate human steps.
- **No unsupported assertions.** A fact with no citation cannot appear in a section — it is
  an open item. Silence beats an unsourced claim.
- **A profile is facts, not a view.** No rating, recommendation, price target, or "buy/sell"
  language — that is research/advice territory and out of scope.
- **MNPI is a legal barrier, not a formatting choice.** External profiles exclude MNPI;
  inclusion requires wall-crossing and is a human/compliance decision.
- **Trading data is time-stamped.** A price past its as-of is `stale` and flagged for
  refresh, never presented as current.
- **Template and required-approvals are versioned.** Record the versions on every manifest so
  the draft is reproducible and reviewable.
