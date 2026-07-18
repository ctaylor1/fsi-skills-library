---
name: market-sizing-builder
description: >-
  Build a transparent TAM/SAM/SOM market-sizing model with explicit driver assumptions, using
  both top-down and bottom-up methods, low/base/high scenarios, a ranked source hierarchy, and
  method triangulation. Use when an investment-banking, equity/credit-research, or corporate
  strategy analyst asks to "size this market", "estimate the TAM/SAM/SOM", "build a bottom-up
  market model", "how big is this market", or needs a sourced, reproducible sizing exhibit for
  a pitch, initiation, or diligence pack. This skill models and reconciles market size with
  cited assumptions and uncertainty ranges; it NEVER gives investment advice, issues a
  buy/sell/hold rating or price target, values a security, guarantees revenue or market share,
  or delivers the exhibit externally without human approval.
license: MIT
compatibility: Amazon Quick Desktop; requires market/financial-data, filings, research-corpus, entity-resolution, document-intelligence, and approved-calculation MCP integrations (all read-only), plus spreadsheet/presentation export.
metadata:
  aws-fsi-category: "Investment Banking & Research"
  aws-fsi-skill-type: "Artifact-creation skills"
  aws-fsi-risk-tier: "R2"
  aws-fsi-archetype: "Model & calculate"
  aws-fsi-agent-pattern: "Interactive production copilot"
  aws-fsi-delivery-wave: "Wave 2 - analytical production"
  aws-fsi-action-mode: "Draft-only; no system-of-record change"
  aws-fsi-scheduled-agent: "no"
  aws-fsi-baseline-status: "new"
  aws-fsi-human-approval: "external-delivery"
  aws-fsi-data-classification: "Highly Confidential (MNPI / client-confidential)"
  aws-fsi-jurisdictions: "US (default); configure additional jurisdiction packs per deployment"
  aws-fsi-owner: "Investment Banking / Research"
  aws-fsi-primary-user: "Investment-banking / research / strategy analyst"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-07-17"
---

# Market Sizing Builder

## Purpose and outcome
Given a defined market and a set of sourced driver assumptions, build a **transparent
TAM/SAM/SOM model** by two independent methods — **top-down** (total market narrowed by
serviceable and obtainable ratios) and **bottom-up** (segment units × price, narrowed by
attach and capture rates) — across **low/base/high** scenarios. Reconcile the two methods
(triangulation), tie out every formula, tag every assumption with its provenance and source
tier, and emit a reproducible sizing exhibit. A successful output gives an analyst a defensible,
source-linked market size with an explicit uncertainty range that can be dropped into a pitch,
initiation, strategy, or diligence deliverable — with the analytical judgment and any external
delivery remaining human.

## Use when
- "Size the US SMB payroll software market" / "What's the TAM/SAM/SOM here?"
- "Build a bottom-up market model from segment units and ARPU."
- "Triangulate a top-down and bottom-up estimate and show the gap."
- "Give me low/base/high market-size scenarios with the sources for each driver."
- An analyst needs a reproducible, cited sizing exhibit for a pitch, initiation, or CIM.

## Do not use
- The user wants a **security valuation**, **price target**, **buy/sell/hold rating**, or
  **investment recommendation** → out of scope (prohibited for this R2 skill). Route to a
  licensed research/banking professional; for a cash-flow valuation model route to `dcf-modeler`.
- The user wants a **qualitative industry/theme map** (value chain, competitors, regulation)
  rather than a quantified size → `market-landscape-researcher`.
- The user wants **scenario/sensitivity/breakeven analysis around operating drivers** of a
  specific model → `scenario-sensitivity-generator`.
- The user wants a **full revenue build inside an integrated model** → `three-statement-model-builder`
  or `dcf-modeler` (consume this skill's SOM/SAM as a bound, do not re-derive it here).
- The user wants the sizing **assembled into a pitch book** → `investment-banking-pitch-builder`.

## Adjacent-skill handoffs
See [references/handoffs.md](references/handoffs.md). This skill emits a durable `sizing_id`
sizing exhibit; downstream modeling, research, and packaging skills consume it. It must not
duplicate their valuation, forecasting, or deck-assembly steps, and it never issues a rating.

## Inputs and prerequisites
- A **defined market** (product/service, geography, segment definitions) and the `as_of` date.
- **Top-down drivers**: a `total_market` magnitude plus `sam_ratio` and `som_ratio`, each with
  low/base/high values, `provenance`, and `source_tier`.
- **Bottom-up drivers**: one row per **segment** with `units`, `arpu`, `attach_rate`, and
  `capture_rate`, each with low/base/high values, `provenance`, and `source_tier`.
- **Config** (versioned): scenario list, `primary_method`, `triangulation_tolerance_pct`,
  numeric `tolerance`. Schema and rules: [scripts/validate_input.py](scripts/validate_input.py),
  [references/domain-rules.md](references/domain-rules.md).
- Read access to market/financial data, filings, and the research corpus for provenance.

## Source hierarchy
See [references/source-map.md](references/source-map.md). Official statistics and regulator data
rank highest for the market universe; company filings for actuals/pricing; third-party research
for industry aggregates; management/internal figures and analyst estimates rank lowest and must
be labeled as such. Every driver cites a source and a tier; conflicts are cited, not silently
resolved. The lowest-tier driver in each chain is the one to stress in the range.

## Workflow
1. **Scope the market** — confirm the market definition, currency, `as_of`, and segment
   boundaries; agree the scenario set. Validate with `validate_input` (fails closed on missing
   scenario values, out-of-range ratios, non-positive magnitudes).
2. **Assemble sourced drivers** — for each driver, record low/base/high with `provenance` and
   `source_tier`. Do not invent figures; if a value is an internal assumption, tag it as such.
3. **Compute (deterministic)** — run
   [scripts/calculate_or_transform.py](scripts/calculate_or_transform.py) to build both methods
   for every scenario, with per-scenario TAM/SAM/SOM, segment detail, tie-outs, and the
   assumptions register.
4. **Triangulate** — the engine reconciles top-down vs bottom-up per level per scenario and
   flags each gap against `triangulation_tolerance_pct`. Investigate any out-of-tolerance gap:
   it usually means a driver (often ARPU, attach, or the total-market source) needs revisiting.
5. **Report** — the configured `primary_method` supplies the headline figures; the other method
   is the cross-check. Present low/base/high with the range and the dominant uncertainty driver.
6. **Write the exhibit** — plain-language summary + both methods + triangulation + the
   assumptions register (with tiers) + explicit uncertainties + the standing disclaimer.

## Validation loop
Run `validate_input` before and [scripts/validate_output.py](scripts/validate_output.py) after.
The output check confirms: both methods present for every scenario; top-down and bottom-up
**formula tie-outs** recompute; **containment** SOM ≤ SAM ≤ TAM holds per method/scenario;
**scenario behavior** is ordered low ≤ base ≤ high per level; the **triangulation** gaps and
flags are internally consistent; reported headline equals the primary method; every assumption
carries provenance and source tier; no investment-advice/rating/price-target/guarantee language;
and the disclaimer is present. Fail closed on any miss and correct before presenting.

## Human approval
`external-delivery`: human review by the deal/coverage team is required before the sizing
exhibit is delivered to a client or written to a data room / system of record. No approval is
needed for the analyst's own internal read. The skill produces a **draft artifact only** — it
makes no system-of-record change.

## Failure handling
- **Thin or missing segmentation** (one bottom-up segment, or segments that don't span the
  market) → `validate_input` warns; state that coverage is incomplete and the bottom-up total
  is a floor, not a full market.
- **Out-of-tolerance triangulation** → do not paper over the gap; report both methods, name the
  likely driver, and widen the range rather than forcing a single point.
- **Low-tier-only drivers** (all internal assumptions, no external anchor) → flag that the size
  is assumption-driven and low-confidence; do not present a false precision.
- **Non-monotonic driver values** (low > base or base > high) → `validate_input` warns and the
  ordering tie-out will fail closed; fix the driver before presenting.
- **Ambiguous market definition** → stop and confirm scope; never size a different market than
  the one asked for.
- **Tool timeout** → return the scenarios computed so far with a clear "incomplete" flag.

## Output contract
1. **Summary** — market, currency, `as_of`, primary method, and base-case TAM/SAM/SOM with the
   low–high range.
2. **Methods** — top-down and bottom-up, each with per-scenario TAM/SAM/SOM (bottom-up with
   segment detail) and its tie-outs.
3. **Triangulation** — per level/scenario gap and in/out-of-tolerance flag, with commentary on
   any divergence.
4. **Assumptions register** — every driver with low/base/high, `provenance`, and `source_tier`.
5. **Uncertainty** — the dominant low-tier driver(s) and what would tighten the estimate.
6. **Machine-readable** — the full sizing JSON with `sizing_id` and `config_version` for
   downstream skills.
7. **Standing disclaimer** — "Market-size estimates for analytical purposes only; not
   investment advice, not a recommendation to buy, sell, or hold any security, and not a
   guarantee of revenue or market share. Estimates depend on the stated assumptions and sources
   and will vary."
See [references/controls.md](references/controls.md).

## Privacy and records
MNPI / client-confidential. Treat the market definition, drivers, and any data-room figures as
material non-public information: minimize to what the exhibit needs, do not commingle across
engagements, and honor information barriers. Retain the sizing exhibit + assumptions register +
`config_version` per records policy; log the read and any external-delivery approval. Never
exfiltrate client or data-room content.

## Gotchas
- **A size is not a recommendation.** A large TAM never implies "buy"; this skill sizes markets
  and stops — ratings, valuations, and advice belong to licensed humans.
- **Triangulation hides in the ratios.** Top-down and bottom-up can agree on TAM yet diverge on
  SOM because the obtainable-share and capture-rate assumptions are the softest inputs — stress
  those, not the total-market anchor.
- **Double-counting segments** inflates the bottom-up total; confirm segments are mutually
  exclusive before summing.
- **Source-tier discipline.** An analyst estimate dressed as an "industry figure" is the most
  common provenance error; every driver's tier is explicit and the lowest tier drives the range.
- **Scenarios are ranges, not probabilities.** Low/base/high are documented assumption sets, not
  a confidence interval — never present them as odds of an outcome.
- **Config, not per-deal tuning.** Scenario definitions, tolerances, and the primary method come
  from the versioned config, not from reverse-engineering a number the client wants to see.
