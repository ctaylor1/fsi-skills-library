---
name: fund-fact-sheet-builder
description: >-
  Assemble a controlled DRAFT fund fact sheet from approved inputs — fund summary, standardized
  net-of-fees performance, holdings, risk, fees, ESG, required disclosures, and a
  source-to-output reconciliation ledger — mapping every figure to its system of record and
  reconciling each number to source. Use when a product, marketing, or performance analyst asks
  to build or refresh a fund/share-class fact sheet, map figures to the template, reconcile
  fact-sheet numbers to source, or list what is missing, unsourced, unreconciled, or unapproved
  before compliance review. HARD BOUNDARY: draft-only — never sends, submits, publishes, or
  distributes the sheet, never promises or guarantees returns, never gives investment advice, a
  rating, or a recommendation, never asserts an unsourced or unreconciled figure, and never
  includes MNPI/embargoed content in an external sheet. Verification, compliance review,
  registered-principal approval, and delivery stay with humans via the approval broker.
license: MIT
compatibility: Amazon Quick Desktop; requires PMS/OMS, market-data, risk/performance-analytics, research-corpus, controlled-content/compliance-rules, entity-resolution, document-intelligence, and reporting/export MCP integrations (all read-only).
metadata:
  aws-fsi-category: "Asset Management"
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
  aws-fsi-owner: "Asset Management investment & product"
  aws-fsi-primary-user: "Product / marketing / performance analyst"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-07-17"
---

# Fund Fact Sheet Builder

## Purpose and outcome
Assemble a **draft** fund fact sheet for a fund/share-class from approved facts: fund summary,
standardized net-of-fees performance, top holdings/allocation, risk metrics, fees/charges, ESG
classification, required regulatory disclosures, and a **source-to-output reconciliation
ledger**. Every asserted figure is mapped to its section, carries a citation, and — where
numeric — ties to its system-of-record value within tolerance. Anything unsourced,
unreconciled, stale, identity-mismatched, MNPI-restricted, or missing a required disclosure is
routed to an **open-items** list instead of being asserted. The outcome is a review-ready draft
plus an explicit gap list — the analyst edits, performance/compliance verify, a registered
principal approves, and a human distributes. This skill never distributes, promises returns,
advises, rates, or fabricates.

## Use when
- "Build/refresh the fact sheet for {fund} {share class} as of {date}."
- "Map these performance, holdings, risk, and fee figures to the fact-sheet template."
- "Reconcile the fact-sheet numbers to the performance/PMS source and show the tie-out."
- "What's missing, unsourced, unreconciled, or unapproved before this goes to compliance?"

## Do not use
- **Performance/attribution calculation** (returns, contribution, attribution) →
  `performance-attribution-builder` (fact sheet cites its verified outputs, never recomputes).
- **Portfolio exposure/holdings analysis** → `portfolio-exposure-analyzer`.
- **Fund narrative / market commentary** → `fund-commentary-drafter`.
- **Liquidity / risk stress analysis** → `liquidity-stress-analyzer`.
- **Mandate/guideline breach monitoring** → `mandate-compliance-monitor`.
- **IC memo** or **DDQ/RFP response** deliverables → `investment-committee-memo-builder`,
  `due-diligence-questionnaire-responder`.
- Any **return promise/guarantee, investment advice, rating, or recommendation**, any
  **distribution/delivery**, or **MNPI in an external fact sheet** → refuse; these are
  human/compliance-owned (see below).

## Adjacent-skill handoffs
See [references/handoffs.md](references/handoffs.md). Fact-sheet assembly is a distinct control
activity from performance calculation, exposure analysis, and commentary drafting. This skill
emits a durable `factsheet_id` plus an assembled manifest, a reconciliation ledger, and an
open-items list; upstream skills and humans supply the verified figures rather than having this
skill recompute them. It never performs the performance analyst's calculation or the principal's
approval and distribution.

## Inputs and prerequisites
- Intake bundle: `factsheet_id`, `fund` (fund_id, legal_name, share_class, isin, ticker,
  currency, inception_date, benchmark_name, objective), `as_of_date`, `intended_distribution`
  (`internal` | `external`), `required_sections`, `required_approvals`, `required_disclosures`,
  `facts[]` (each: `section`, `fact_id`, `label`, `value`, optional `value_numeric` +
  `source_value_numeric` + `reconcile_tolerance`, `source_ref`, `effective_date`, optional
  `expires`, `mnpi`, `basis`, `fund_id`), `disclosures[]` (approved text + citation), and any
  recorded `approvals[]`. Schema: [scripts/validate_input.py](scripts/validate_input.py).
- Read access to PMS/OMS, market data, risk/performance analytics, research corpus,
  controlled-content library, entity resolution, and document intelligence. **Read-only.**

## Source hierarchy
See [references/source-map.md](references/source-map.md). The performance system is
authoritative for returns; PMS/OMS for holdings and fees; risk analytics for risk metrics;
market data for time-sensitive figures (as-of dated); the controlled-content library for
approved disclosure text. Every asserted figure carries `{system}:{ref}@{date/version}` and,
where numeric, a source value to reconcile against. Required sections, required approvals,
required disclosures, and the fact-sheet template are **versioned contracts**.

## Workflow
1. **Validate & normalize** — run `validate_input`; confirm structure, dedupe `fact_id`s, and
   surface data gaps (unsourced figures, undated figures, figures that cannot be reconciled,
   MNPI-in-external warnings, missing required disclosures).
2. **Assemble & reconcile (deterministic)** — run
   [scripts/calculate_or_transform.py](scripts/calculate_or_transform.py): map each fact to its
   section, reconcile every numeric figure to its source value, and assign a status —
   `included`, `stale` (past `expires` vs `as_of`), `unresolved` (fund-identity mismatch),
   `restricted` (MNPI in an external sheet), `unsupported` (no citation), or a reconcile break
   (figure does not tie to source). Only `included`/`stale`/`unresolved` are asserted; the rest
   are **routed to open items, never asserted**. Build the source reconciliation ledger.
3. **Render disclosures** — place each required regulatory disclosure as approved, cited
   controlled content; uncited or missing required disclosures become open items.
4. **Capture approvals** — record recorded approvals (role, date, citation); mark
   required-but-missing approvals (performance verification, compliance/marketing review,
   registered-principal approval) as **outstanding** open items.
5. **List open items** — unsourced/unreconciled figures, stale data, identity mismatches, MNPI
   exclusions, incomplete required sections, missing disclosures, and outstanding approvals —
   each with the required human action.
6. **Render to template** — populate [assets/output-template.md](assets/output-template.md);
   `assembly_status` stays `draft-assembled`.
7. **Never distribute / promise / advise** — no send/submit/publish, no return
   promise/guarantee, no rating/recommendation.

## Validation loop
Run `validate_input` before and [scripts/validate_output.py](scripts/validate_output.py) after.
The output check enforces: all required template sections present; **no unsupported
assertions** (every asserted figure carries a citation); **every asserted numeric figure ties
to source** within tolerance (no unreconciled figure presented); **no MNPI** in an external
sheet; rendered disclosures are cited (no unsupported disclosure); required approvals recorded
(role/date/citation) with delivery approval flagged required; no return-promise/guarantee,
investment-advice/rating/recommendation, or distribution/delivery language;
`assembly_status: draft-assembled`; standing note present. Fail closed on any miss.

## Human approval
`external-delivery`. Internal analytical drafting is reviewer-sampled; **before any external
distribution or system-of-record change**, performance measurement must verify the numbers,
compliance/marketing must review the communication, a registered principal must approve, and a
human distributes via the approval broker. This skill proposes a draft and a gap list — humans
verify, approve, and deliver.

## Failure handling
- **Unsourced figure** → `unsupported` open item ("attach an approved source or remove the
  figure"); never asserted, never fabricated to fill a section.
- **Figure does not tie to source** → reconcile-break open item; the figure is **not** asserted
  until it is reconciled to its system of record. A number that does not tie out is never shown.
- **Stale risk/market data** → `stale`; keep cited, flag for refresh as of the reporting date.
- **Ambiguous / mismatched fund or share class** → `unresolved`; reconcile with a human, never
  auto-merge.
- **MNPI / embargoed content in an external sheet** → excluded and flagged for wall-crossing /
  compliance clearance; never silently included.
- **Missing required disclosure / incomplete required section** → open item; do not pad with
  unsourced content or omit a required disclosure silently.
- **Tool timeout / partial data** → return the partial draft with an explicit incomplete flag;
  assume no retry.

## Output contract
1. **Fact-sheet manifest** — `sections{fund_summary, performance, holdings, risk, fees, esg,
   reconciliation, disclosures, approvals, open_items, sources}`; each asserted entry carries
   `status` + `citation`.
2. **Source reconciliation ledger** — every numeric figure with its output value, source value,
   delta, tolerance, and tie-out result.
3. **Open-items list** — every gap (unsourced, reconcile-break, stale, unresolved,
   MNPI-excluded, section-incomplete, missing-disclosure, outstanding-approval) with the
   required human action.
4. **Approvals** — recorded (role/date/citation) and outstanding.
5. **Machine-readable** — the manifest keyed by `factsheet_id`; `assembly_status:
   draft-assembled`, `human_approval_required_before_delivery: true`.
6. **Standing note** — "Draft fund fact sheet for human review only. Every figure is
   source-cited and reconciled to its system of record, past performance is not indicative of
   future results, and this fact sheet has not been reviewed, approved, or distributed."
See [references/controls.md](references/controls.md) and
[references/domain-rules.md](references/domain-rules.md).

## Privacy and records
**Highly Confidential (MNPI / client-confidential).** Treat pre-publication figures, undisclosed
positions, and embargoed content as confidential; MNPI never enters an external fact sheet
without documented wall-crossing / compliance clearance. Mask internal fund/account identifiers
to what the sheet needs; public identifiers (legal name, ISIN, ticker) may appear. Retain the
manifest, reconciliation ledger, open items, approvals, and citations with the template/config
versions; log every read and assembly with the analyst identity.

## Gotchas
- **Assembly ≠ verification ≠ approval ≠ distribution.** A `draft-assembled` sheet is not
  performance-verified, compliance-reviewed, principal-approved, or sent; those are separate
  human steps.
- **A number that does not tie out is not shown.** Source-to-output reconciliation is the point:
  an unreconciled figure is an open item, never a fact-sheet line.
- **No unsupported assertions.** A figure with no citation cannot appear in a section — it is an
  open item. Silence beats an unsourced number.
- **A fact sheet states facts, not a view.** No return promise or guarantee, no rating,
  recommendation, or "buy/sell" language — that is advice/marketing-claim territory and out of
  scope. Past performance is not indicative of future results.
- **Performance must be standardized.** Present net-of-fees, standardized-period returns; a
  gross-only or non-standard figure is flagged for review, never presented as the headline.
- **MNPI is a legal barrier, not a formatting choice.** External sheets exclude MNPI/embargoed
  content; inclusion requires wall-crossing and is a human/compliance decision.
- **Template, disclosures, and required approvals are versioned.** Record the versions on every
  manifest so the draft is reproducible and reviewable.
