---
name: comps-analysis-builder
description: >-
  Build and refresh a comparable-company (trading comps) analysis: assemble sourced operating
  metrics, construct enterprise-value bridges, compute trading multiples (EV/Revenue, EV/EBITDA,
  EV/EBIT, P/E on LTM and forward), flag non-meaningful and outlier multiples, compute peer
  summary statistics, derive an implied-value cross-check range, document peer rationale, and run
  QA tie-outs — as a source-linked draft for analyst and banker review. Use when an
  investment-banking or equity-research analyst asks to build, refresh, or QA a comps set, spread
  peer multiples, compute EV bridges, or produce a market-multiple valuation cross-check with
  citations. HARD BOUNDARY: draft-only — never issues a recommendation, rating, or price target;
  never states a valuation or fairness opinion; never fabricates a metric or picks peers outside
  the versioned criteria; never misuses MNPI; never sends or delivers. It assembles and cites;
  humans conclude value and deliver.
license: MIT
compatibility: Amazon Quick Desktop; requires filings/document-intelligence, market/financial-data, estimates/research-corpus, CRM, data-room, and approved-config MCP integrations (all read-only).
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
  aws-fsi-primary-user: "Investment-banking / equity-research analyst"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-07-17"
---

# Comps Analysis Builder

## Purpose and outcome
Turn a subject company and a peer set into ONE **source-linked comparable-company analysis
draft**. For the subject and every peer the skill builds a cited enterprise-value bridge
(`market_cap + debt + preferred + minority - cash`), computes trading multiples (EV/Revenue,
EV/EBITDA, EV/EBIT, P/E on LTM and forward FY1), flags each multiple as `meaningful`, `nm`
(non-positive denominator), `missing`, or `outlier`, excludes stale-priced and excluded peers
from the statistics, computes summary statistics (min/Q1/median/mean/Q3/max), derives an
implied-value **cross-check range** for the subject, runs deterministic QA tie-outs, and lists
open items — every asserted figure carries a citation. The outcome is an analysis a human can
review and route: a rendered analysis from [assets/output-template.md](assets/output-template.md)
plus a machine-readable manifest. The skill **assembles and cites**; it does not conclude value,
recommend, or deliver.

## Use when
- "Build / refresh the trading comps for this subject against these peers."
- "Compute the EV bridges and EV/EBITDA, EV/Revenue, and P/E multiples for this peer set."
- "Give me the peer median and mean multiples with citations and an implied range for the subject."
- "QA this comps set — which multiples are non-meaningful or outliers, and what's stale or missing?"
- "Document the peer-selection rationale and flag anything that needs human confirmation."

## Do not use
- **Intrinsic DCF valuation** (WACC, terminal value, forecast drivers) → `dcf-modeler`.
- **Building the underlying projections** (integrated model, forward estimates) →
  `three-statement-model-builder`; **market/TAM sizing** → `market-sizing-builder`.
- **Post-earnings beat/miss analysis** of reported results → `earnings-results-analyzer`.
- **Independent review** of valuation methods, inputs, and comparables → `valuation-reviewer`.
- **Assembling the client pitch book** → `investment-banking-pitch-builder`;
  **industry/peer-universe mapping** → `market-landscape-researcher`.
- Any **investment recommendation, rating, price target, or binding valuation/fairness opinion**
  → refuse; the valuation conclusion is a licensed, human-owned deliverable.

## Adjacent-skill handoffs
See [references/handoffs.md](references/handoffs.md). Building the comps set is deliberately
separated from intrinsic modeling, from the valuation conclusion / independent review, and from
assembling a client deliverable (distinct controls, accountability, and reliance). This skill
emits a durable `analysis_id` + cited manifest and hands off to `dcf-modeler` (intrinsic
cross-check), `valuation-reviewer` (independent review), and `investment-banking-pitch-builder`
(deliverable); it must not perform their work or a human's valuation conclusion.

## Inputs and prerequisites
- The intake bundle: `analysis_id`, `as_of_date`, `currency`, `units`, versioned
  `peer_selection_criteria`, `config` (freshness threshold, `min_peers`, multiple `bands`,
  `implied_multiples`), `required_approvals`, recorded `approvals`, the `subject`, and the
  `peers` — each company with price/shares/price_date, debt/cash/preferred/minority, LTM and
  forward metrics, and `source_ref`/`market_source_ref`. Schema and required fields:
  [scripts/validate_input.py](scripts/validate_input.py).
- Read access to filings/document intelligence, market/financial data, estimates, CRM, and
  (permission-gated) data room. No figure is fabricated: what is not supplied becomes a
  non-meaningful multiple and a missing-metric open item.

## Source hierarchy
See [references/source-map.md](references/source-map.md). Filings win on reported fundamentals;
market data is the authority on price and share count; the versioned selection criteria are the
authority on which companies are peers. Cite every asserted figure as `{system}:{ref}@{date}`.
`peer_selection_criteria`, the multiple `bands`, and the template are **versioned contracts**.

## Workflow
1. **Validate & normalize** — run `validate_input`; confirm structure and surface data gaps
   (missing metrics, non-positive denominators, stale prices, currency mismatches, thin peer
   set) as warnings.
2. **Build the analysis (deterministic)** — run
   [scripts/calculate_or_transform.py](scripts/calculate_or_transform.py): construct each EV
   bridge, compute and classify multiples, exclude stale/excluded peers from the statistics,
   compute summary statistics, derive the implied cross-check range, and run QA tie-outs. Rules:
   [references/domain-rules.md](references/domain-rules.md).
3. **Render the analysis** — populate [assets/output-template.md](assets/output-template.md) from
   the manifest; every bridge, multiple, and implied value carries its citation/basis.
4. **Compile open items** — everything not `meaningful` (missing metrics, `nm`, outliers, stale
   data, excluded peers, currency mismatches, thin set, outstanding approvals) becomes an
   explicit open item. Do not silently drop, infer, or steer.
5. **Mark draft & hand off** — set `build_status: draft-comps`, record that human approval is
   required before delivery, and route to `dcf-modeler` / `valuation-reviewer` /
   `investment-banking-pitch-builder`. Never conclude value, recommend, or send.

## Validation loop
Run `validate_input` before and [scripts/validate_output.py](scripts/validate_output.py) after.
The output check enforces: all required template sections present; every EV bridge and multiples
row cited and every implied value tied to an existing statistic basis (no unsupported claims);
deterministic tie-outs hold (`market_cap` and `enterprise_value` reconcile); approvals recorded
with role/date/citation and delivery approval flagged; no recommendation/rating/price-target,
valuation/fairness-opinion, MNPI, or send/deliver language; `build_status` is `draft-comps`;
standing note present. Fail closed on any miss.

## Human approval
`external-delivery`. This skill produces a **draft** analysis for internal review. A human must
review and approve before the analysis is delivered externally, relied on for a valuation
conclusion, or treated as a system-of-record change. The valuation conclusion, any
recommendation, and external delivery are separate, human-owned steps — this skill neither
performs nor pre-empts them.

## Failure handling
- **Missing operating metric** → multiple `missing`; missing-metric open item; never fabricated.
- **Non-positive denominator** (e.g. negative EBITDA) → multiple `nm`; excluded from statistics.
- **Outlier multiple** (outside the configured band) → shown, flagged, excluded from statistics;
  confirm-exclusion open item.
- **Stale market data** (`price_date` older than the freshness threshold) → company `stale`;
  computed and cited but excluded from statistics; refresh open item.
- **Currency mismatch** → open item to FX-normalize before comparison; never silently mixed.
- **Thin peer set / no meaningful values** → statistic reported not-derivable with an open item;
  no guessing.
- **Unresolvable data / tool timeout** → return the partial analysis with an explicit incomplete
  flag and the open-items list; no retry assumption.

## Output contract
See [references/controls.md](references/controls.md) and
[assets/output-template.md](assets/output-template.md).
1. **Rendered analysis** — the template sections (analysis summary, subject company, peer set, EV
   bridges, trading multiples, summary statistics, implied valuation, QA checks, open items,
   approvals, source index) populated with cited content.
2. **Machine-readable manifest** — `analysis_id`, per-company EV bridge + multiples with
   flags/citations, summary statistics, implied cross-check range with basis, QA tie-outs,
   approvals (recorded/outstanding), open items, source index, `build_status` (`draft-comps`),
   and `human_approval_required_before_delivery: true`.
3. **Open-items list** — every missing/nm/outlier/stale/excluded/mismatch/outstanding item with a
   required human action.
4. **Standing note** — "Draft comparable-company analysis for human review only. It is not
   investment advice, not a research rating or price-target, and not a valuation or fairness view;
   the multiples and any implied ranges are an analytical cross-check, and this draft has not been
   reviewed, approved, or delivered."

## Privacy and records
**Highly Confidential — MNPI / client-confidential.** Enforce information barriers; use
data-room (non-public) figures only when the requesting user is wall-crossed and permissioned,
and never disclose selectively. Mask approver and internal identifiers in output. Retain the
analysis manifest, citations, and config/template versions per the firm's research/deal
recordkeeping policy; log the analyst identity on every read and build. Data stays within the
deployment's residency boundary.

## Gotchas
- **Comps ≠ valuation conclusion.** Multiples and an implied range are a market cross-check, not
  a statement of what the company is worth. The valuation conclusion and any recommendation are
  human-owned (see `valuation-reviewer` for independent review, `dcf-modeler` for the intrinsic
  cross-check).
- **`nm`/`missing`/`outlier` are per multiple, not per company.** A loss-making peer can be a
  meaningful EV/Revenue comp while its EV/EBITDA is `nm` — do not drop the whole company.
- **Statistics use the clean set.** Subject, `nm`, `missing`, outlier, and stale-priced values are
  excluded from median/mean; report `n` so reviewers see the basis.
- **No peer cherry-picking.** Inclusion/exclusion follows the versioned criteria and every entry
  is cited and human-confirmable; excluded peers are open items, not silent drops.
- **No figure is invented.** A missing metric is a non-meaningful multiple and an open item, never
  an assumed value. Every asserted number must tie out and be citable.
- **Mind the wall.** Use non-public data-room figures only for a wall-crossed, permissioned user;
  never disclose or infer MNPI.
- **Versioned contracts.** Record `config_version`, the selection criteria, `bands`, and template
  version on the manifest so the analysis is reproducible and reviewable.
