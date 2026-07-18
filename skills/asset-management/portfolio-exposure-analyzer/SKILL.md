---
name: portfolio-exposure-analyzer
description: >-
  Analyze a portfolio's exposures across issuer, sector, country, currency, asset class,
  duration, liquidity, factor, and look-through holdings, screen each against documented
  concentration limits, and assemble source-linked findings with a suggested review
  priority. Use when a portfolio manager or risk analyst asks "what is my exposure to X",
  "where am I over a concentration limit", "break down this fund by sector/country/currency",
  "show issuer exposure on a look-through basis", or needs a cited exposure pack for review.
  This skill explains and evidences exposures and proposes a review priority; it NEVER makes
  a mandate-compliance determination, recommends or executes a trade/rebalance/hedge, or
  gives personalized investment advice — those are human / mandate-compliance / licensed
  actions.
license: MIT
compatibility: Amazon Quick Desktop; requires PMS/OMS-holdings, market-and-reference-data, look-through/fund-constituent, risk/factor-model, and versioned-guidelines-config MCP integrations (all read-only).
metadata:
  aws-fsi-category: "Asset Management"
  aws-fsi-skill-type: "Analysis and evaluation skills"
  aws-fsi-risk-tier: "R2"
  aws-fsi-archetype: "Analyze & review"
  aws-fsi-agent-pattern: "Interactive decision-support copilot"
  aws-fsi-delivery-wave: "Wave 2 - analytical production"
  aws-fsi-action-mode: "Read-only analysis"
  aws-fsi-scheduled-agent: "no"
  aws-fsi-baseline-status: "new"
  aws-fsi-human-approval: "external-delivery"
  aws-fsi-data-classification: "Highly Confidential (MNPI / client-confidential)"
  aws-fsi-jurisdictions: "US (default); configure additional jurisdiction packs per deployment"
  aws-fsi-owner: "Asset Management investment & product"
  aws-fsi-primary-user: "Portfolio manager / risk analyst"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-07-17"
---

# Portfolio Exposure Analyzer

## Purpose and outcome
Given a portfolio's holdings, compute **explainable exposures** across issuer, sector,
country, currency, asset class, duration, liquidity, factor, and **look-through** holdings;
screen each against **documented concentration limits**; attach cited evidence to every
number; and produce a review-ready pack with a **suggested review priority**. A successful
output lets a portfolio manager or risk analyst see where concentrations sit and where they
exceed documented limits — the compliance determination and any portfolio action remain
human.

## Use when
- "What is my look-through exposure to issuer X?"
- "Break this fund down by sector / country / currency / duration / liquidity, with sources."
- "Where am I over a single-issuer, sector, or illiquidity limit?"
- A reviewer needs a consistent, cited exposure write-up to attach to an IC memo or review.

## Do not use
- The user wants a **mandate-compliance determination** ("are we in breach?"), a guideline
  test of a proposed trade, or an exception escalation → `mandate-compliance-monitor` (and a
  human compliance officer).
- The question is **stressed liquidity / liquidation horizon / redemption coverage** →
  `liquidity-stress-analyzer`.
- The question is **counterparty / settlement / derivative / collateral** exposure and limit
  monitoring → `counterparty-exposure-monitor`.
- The user wants **return attribution** (allocation/selection/factor), not current exposure →
  `performance-attribution-builder`.
- The user wants a **trade, rebalance, or hedge** recommended or executed → out of scope for
  every skill in this library without human authorization; route to the portfolio manager.

## Adjacent-skill handoffs
See [references/handoffs.md](references/handoffs.md). This skill emits an exposure pack with
a durable `exposure_id`; downstream compliance, liquidity, attribution, and drafting skills
consume it. It must not duplicate their determination, modeling, or action steps.

## Inputs and prerequisites
- Portfolio identifier and `as_of` date.
- **Holdings** with, per position: `position_id`, `instrument_id`, `asset_class`,
  `market_value` (already in base currency), and where available `issuer`, `sector`,
  `country`, `currency`, `modified_duration`, `liquidity_days`, `factors`, and
  `look_through` constituents. Schema: [scripts/validate_input.py](scripts/validate_input.py).
- Read access to PMS/OMS, market/reference data, look-through, and the risk model; the
  versioned limits config (see [references/domain-rules.md](references/domain-rules.md)).

## Source hierarchy
See [references/source-map.md](references/source-map.md). PMS/OMS holdings are the position
of record; market/reference data classifies and prices; look-through decomposes pooled
vehicles; the risk model supplies duration/factor/liquidity; versioned config supplies
limits. Cite every exposure and finding to a source row.

## Workflow
1. **Scope & validate** — confirm the portfolio and `as_of`; load holdings; run
   `validate_input`. Note any dimension rendered not-evaluable by missing data.
2. **Compute exposures (deterministic)** — run
   [scripts/calculate_or_transform.py](scripts/calculate_or_transform.py) to aggregate every
   dimension, applying **look-through** so pooled-vehicle risk is attributed to underlying
   issuers/sectors/countries/currencies rather than the wrapper.
3. **Screen against documented limits** — the script flags each exposure that exceeds a
   documented concentration limit as a **finding** with its band (`over_soft` / `over_hard`
   / `over_limit`), the limit, the excess, and the contributing positions.
4. **Suggest priority** — map the finding set to a review band (Informational / Review /
   Elevated) per the documented mapping. This is a triage suggestion for a human, explicitly
   **not** a mandate-compliance determination.
5. **Write the pack** — plain-language explanation per exposure/finding + the evidence + the
   suggested priority + explicit considerations (benchmark weights, intended tilts, overlays,
   stale look-through) to weigh before drawing conclusions.

## Validation loop
Run `validate_input` before and [scripts/validate_output.py](scripts/validate_output.py)
after. The output check confirms: every finding has cited evidence, no
determination/action/advice language is present, the priority maps deterministically from the
findings, the standing disclaimer is present, and considerations are included when any
finding fired. Fail closed on any miss.

## Human approval
`external-delivery`: human review required before the pack is sent to a client/IC or written
to a report/system of record. No approval is needed for the analyst's own read. The skill
never takes a portfolio action.

## Failure handling
- **Missing classification (issuer/sector/country/currency)** → compute only the dimensions
  the data supports; label the rest "not evaluable"; never guess a classification.
- **Missing look-through data** → attribute the wrapper to itself as a single issuer and say
  so; do not fabricate constituents.
- **Missing duration/liquidity/factor** → mark those dimensions not-evaluable; do not invent
  a number.
- **Stale constituent/price data** → cite the effective date; flag the lag; do not resolve
  silently.
- **Ambiguous portfolio/as-of** → stop and confirm; never analyze the wrong book.
- **Tool timeout** → return the exposures computed so far with a clear "incomplete" flag.

## Output contract
1. **Summary** — portfolio, `as_of`, NAV, base currency, count of findings, suggested band.
2. **Exposures** — per dimension: ranked buckets with % of NAV and cited contributing rows
   (issuer/sector/country/currency on a look-through basis; duration; liquidity buckets).
3. **Findings** — per exposure over a documented limit: dimension, bucket, %, limit, excess,
   band, and cited evidence.
4. **Considerations** — benchmark weights vs active exposure, intended tilts, overlays,
   stale look-through, sovereign/cash exemptions.
5. **Not-evaluable dimensions** — with the reason (e.g., factor requires the risk model).
6. **Machine-readable** — exposures + findings + `exposure_id` for downstream skills.
7. **Standing disclaimer** — "Exposure analysis and evidence only; not a mandate-compliance
   determination or investment advice. No trade or portfolio action has been taken or
   recommended."
See [references/controls.md](references/controls.md).

## Privacy and records
MNPI / client-confidential holdings. Minimize holdings data in output to what evidences an
exposure. Retain the analysis + citations + `config_version` per records policy; log the read
and any external-delivery approval. Never exfiltrate holdings.

## Gotchas
- **An exposure over a limit is not a breach finding.** It is a factual comparison to a
  *documented limit*; the compliance determination belongs to `mandate-compliance-monitor`
  and a human.
- **Look-through changes the answer.** Issuer/sector/country concentration must decompose
  pooled vehicles, or a fund can hide a large single-issuer position.
- **Active vs absolute.** A large sector weight may simply track the benchmark; present both
  framings and never call a benchmark-driven weight a defect.
- **Sovereign and cash exemptions.** Government bonds and cash are exempt from issuer/sector
  limits by config — a 40% Treasury holding is not a single-issuer finding.
- **Do not tune limits to the portfolio.** Limits come from the versioned config, not from
  guessing what "should" be acceptable for this fund.
