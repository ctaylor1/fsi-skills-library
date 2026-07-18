---
name: portfolio-risk-diversification-check
description: >-
  Compute transparent, explainable portfolio concentration and diversification exposures —
  single-name, top-N, sector, geography, asset-class, factor, correlation, and liquidity —
  with cited evidence and an educational diversification band. Use when a retail investor or
  portfolio analyst asks "how diversified is this portfolio", "is this too concentrated",
  "what are my sector/geography/factor exposures", "run a diversification check", or wants a
  source-linked exposure profile for review. This skill analyzes and educates only; it NEVER
  gives personalized investment advice, a suitability or "good investment" judgment, a
  buy/sell/hold/rebalance recommendation, a return or price forecast, or places any trade —
  those are decisions for a licensed human.
license: MIT
compatibility: Amazon Quick Desktop; requires book-of-record/custody positions, market/reference-data (classification, factor, correlation, liquidity), OMS/EMS, and approved-calculation MCP integrations (all read-only).
metadata:
  aws-fsi-category: "Capital Markets"
  aws-fsi-skill-type: "Guidance or domain-expertise skills"
  aws-fsi-risk-tier: "R2"
  aws-fsi-archetype: "Domain workflow"
  aws-fsi-agent-pattern: "Interactive decision-support copilot"
  aws-fsi-delivery-wave: "Wave 1 - stabilize existing"
  aws-fsi-action-mode: "Read-only analysis"
  aws-fsi-scheduled-agent: "no"
  aws-fsi-baseline-status: "existing-updated"
  aws-fsi-human-approval: "external-delivery"
  aws-fsi-data-classification: "Highly Confidential (customer NPI/PII)"
  aws-fsi-jurisdictions: "US (default); configure additional jurisdiction packs per deployment"
  aws-fsi-owner: "Capital Markets operations & compliance"
  aws-fsi-primary-user: "Retail investor / portfolio analyst"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-07-17"
---

# Portfolio Risk Diversification Check

## Purpose and outcome
Given a portfolio's holdings and weights plus bundled reference data, compute a set of
**explainable diversification/concentration checks** (single-name, top-N, sector, geography,
asset-class, factor tilt, correlation, liquidity), explain in plain language why each
flagged, attach cited evidence to each, and produce a review-ready **exposure profile** with
a descriptive **diversification band**. A successful output lets an investor understand where
a portfolio's exposures are concentrated, or lets an analyst attach a consistent, cited
diversification write-up to a review — the **investment decision remains a human's**, made
with a licensed professional.

## Use when
- "How diversified is this portfolio? Is it too concentrated?"
- "What are my sector / geography / asset-class / factor exposures?"
- "Run a diversification (concentration) check and show me the evidence."
- An analyst needs a reproducible, cited exposure profile to attach to a portfolio review.

## Do not use
- The user wants **personalized investment advice**, a **suitability** judgment, a
  **buy/sell/hold/rebalance recommendation**, a **return/price forecast**, or a financial
  plan → out of scope for every skill in this library. Provide the exposure profile as
  background and route to a **licensed human financial professional**.
- The user wants a **plain summary of holdings** (no concentration/risk analysis) →
  `portfolio-holdings-summarizer`.
- The user wants **one fund/product explained** (fees, strategy, liquidity of a single
  security) → `prospectus-plain-language-breakdown`.
- The user wants a **single trade confirmation** explained → `trade-confirmation-explainer`.
- The concentration/liquidity question is about **collateral/margin** eligibility and
  haircuts, not investment diversification → `margin-collateral-optimizer`.

## Adjacent-skill handoffs
See [references/handoffs.md](references/handoffs.md). This skill emits an exposure profile
with a durable `analysis_id`; consuming/holdings skills reuse it and must not re-label the
educational band as advice. It must not duplicate their summary, explanation, or (nonexistent)
recommendation steps.

## Inputs and prerequisites
- **Portfolio identifier** and an `as_of` date, and the **holdings**: each position with a
  symbol, weight (portfolio fraction), and `source_ref`; optionally asset class, sector,
  region, liquidity days, and factor loadings. Schema:
  [scripts/validate_input.py](scripts/validate_input.py).
- **Reference data** for the checks that need it: a `correlation_matrix` (for correlation),
  `factor_loadings` (for factor tilt), `sector`/`region`/`asset_class` (for those
  concentration checks), and `liquidity_days` (for liquidity). Missing inputs make a check
  `not_evaluable`, never a silent pass.
- Read access to positions and reference data; approved thresholds/config (see
  [references/domain-rules.md](references/domain-rules.md)).

## Source hierarchy
See [references/source-map.md](references/source-map.md). The custody/book-of-record position
is authoritative for what is held and in what weight; classification, factor, correlation, and
liquidity inputs are **model inputs** from reference data, not ground truth. Cite every
flagged check to the specific positions/buckets behind it with the `as_of` date.

## Workflow
1. **Scope & load** — confirm the portfolio and `as_of`; load holdings and the reference
   inputs available; validate with `validate_input`. Note which checks are evaluable.
2. **Compute checks (deterministic)** — run
   [scripts/calculate_or_transform.py](scripts/calculate_or_transform.py) to compute the
   configured checks (single-name, top-N, sector, geography, asset-class, factor tilt,
   correlation, liquidity) plus summary metrics (HHI, effective holdings, top-N weight). Each
   flagged check returns its evidence rows and the threshold behind it. Checks are
   **explainable**, not a black-box score.
3. **Assemble evidence** — for each flagged check, attach the specific positions, bucket, or
   correlation pairs and the configured threshold it exceeds, with citations.
4. **Assign band** — map the flagged-check set to a diversification band (Well-diversified /
   Moderately concentrated / Highly concentrated) per the deterministic, documented mapping.
   This is a **descriptive summary of exposures**, not advice, a suitability rating, or a
   forecast.
5. **Write the profile** — plain-language explanation per flagged check + the evidence + the
   band + `educational_prompts` (context: metrics are model- and window-dependent; fit is a
   question for the investor and a licensed professional) + the standing disclaimer.

## Validation loop
Run `validate_input` before and [scripts/validate_output.py](scripts/validate_output.py)
after. The output check confirms: every flagged check has evidence + citation, the band ties
out to the deterministic mapping, **no advice/recommendation/forecast language** is present,
the standing disclaimer is included, and `educational_prompts` are present when any check
flagged. Fail closed on any miss.

## Human approval
`external-delivery`: human review required before the profile is sent to a client or written
to a system of record. No approval is needed for the analyst's own read. The skill never
places a trade or writes a system of record.

## Failure handling
- **Missing reference inputs** (no correlation matrix / factor loadings / sector / region /
  liquidity) → report those checks as `not_evaluable`; do not overstate or guess concentration.
- **Weights that do not sum to ~1** → warn and confirm whether inputs are portfolio fractions
  before interpreting; do not silently normalize away a data problem.
- **Ambiguous portfolio/identity** → stop and confirm; never analyze the wrong book.
- **Stale/conflicting reference dates** → cite the `as_of` of each input; do not resolve
  silently; label window-dependent figures as estimates.
- **Tool timeout** → return the checks computed so far with a clear "incomplete" flag; page
  large books as resumable stages.

## Output contract
1. **Summary** — portfolio (masked), `as_of`, config version, count of flagged checks,
   diversification band, and key metrics (HHI, effective holdings, top-N weight).
2. **Checks** — per flagged check: name, plain-language reason, evidence rows (cited), and the
   configured threshold it exceeds. Non-flagged evaluable checks and `not_evaluable` checks
   are listed too.
3. **Educational prompts** — context so the reader weighs the band rather than reading it as a
   verdict (strategy intent, model/window dependence, and that fit is for a licensed human).
4. **Machine-readable** — checks + evidence + metrics + `analysis_id` for consuming skills.
5. **Standing disclaimer** — "Educational risk analysis only; not personalized investment
   advice or a recommendation to buy, sell, or hold any security."
See [references/controls.md](references/controls.md).

## Privacy and records
Customer NPI/PII. Mask account/portfolio identifiers (last 4). Minimize customer data in the
output to the holdings and buckets that evidence a flagged check. Retain the analysis +
citations + config version per records policy; log the read and any external-delivery
approval. Never exfiltrate holdings data.

## Gotchas
- **A concentration check is not a decision.** A "Highly concentrated" band justifies a
  closer look and a conversation with a licensed professional — never a buy/sell/rebalance
  recommendation or a suitability verdict from this skill.
- **Concentration can be deliberate.** A focused, informed strategy is not "wrong"; the band
  describes exposures, it does not grade them.
- **Correlations are not fixed.** Pairwise correlations are window-dependent estimates that
  typically **rise in stressed markets** — a portfolio that looks diversified in calm periods
  can concentrate exactly when it matters. State the window; do not present correlations as
  properties of the holdings.
- **Classification is scheme-dependent.** A name can map to different sector/region buckets
  under different taxonomies; cite the taxonomy and `as_of`, and do not treat a bucket as
  ground truth.
- **Weights must be fractions.** If weights are notional amounts rather than portfolio
  fractions, every ratio is wrong — validate the weight sum before interpreting.
- **Do not tune thresholds to the portfolio.** Thresholds come from the versioned config, not
  from choosing a cutoff that produces a desired band.
