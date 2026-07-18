---
name: liquidity-stress-analyzer
description: >-
  Estimate liquidation horizons, market-impact/cost, redemption coverage, collateral and
  margin needs, and stressed liquidity for a portfolio or fund under transparent, fully
  parameterized scenarios, with each metric evidenced to source positions and mapped to a
  suggested liquidity-risk band. Use when a liquidity-risk analyst or portfolio manager asks
  "how long to liquidate this book", "can we cover a redemption of X% under stress", "what is
  the market-impact cost of raising cash", "how much additional margin under a price shock",
  or needs a review-ready liquidity-stress pack for a liquidity risk committee. This skill
  analyzes and evidences liquidity under stated assumptions and proposes a review band; it
  NEVER recommends or executes a trade or liquidation, suspends/gates redemptions, activates a
  side pocket, determines a mandate breach, or gives investment advice — those are
  human/licensed-specialist/authorized-system actions.
license: MIT
compatibility: Amazon Quick Desktop; requires PMS/OMS, market-data, risk/performance, research, compliance-rules, and document/reporting MCP integrations (all read-only).
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
  aws-fsi-primary-user: "Liquidity risk / portfolio management"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-07-17"
---

# Liquidity Stress Analyzer

## Purpose and outcome
Given a portfolio's positions, average daily volumes (ADV), spreads, and a **transparent
liquidity scenario**, compute a set of **explainable liquidity metrics** — liquidation
horizon buckets, market-impact/cost, redemption coverage, and collateral/margin buffer
coverage — attach cited evidence to each, and map the breached-metric set to a **suggested
liquidity-risk band** (Adequate / Watch / Stressed). A successful output lets a liquidity-risk
analyst or portfolio manager understand *how liquid the book is under stated stress* and
lets a liquidity risk committee decide what to do next — the decision, and any trade or
fund-liquidity action, remains human.

## Use when
- "How long would it take to liquidate this book under stress?"
- "Can we cover a 50% redemption within the 7-day notice period?"
- "What is the market-impact cost of raising $X in cash?"
- "How much additional margin would a 10% price shock require, and does our buffer cover it?"
- A liquidity-risk reviewer needs a consistent, cited liquidity-stress pack for a committee.

## Do not use
- The user wants a **decision or action** — "should we gate the fund / suspend redemptions /
  activate a side pocket", "sell the high-yield book", "execute the liquidation" → out of
  scope. Provide evidenced metrics and route to the portfolio manager, liquidity risk
  committee, and dealing/execution desk (human/authorized systems).
- The user wants a **mandate/guideline/regulatory breach determination** (e.g., a UCITS/40-Act
  liquidity-bucket rule finding) → that is `mandate-compliance-monitor` plus human
  compliance sign-off, not this skill.
- **Personalized investment, trading, or tax advice** → out of scope for any skill; refer to
  a licensed professional.
- Exposure decomposition (issuer/factor/sector/liquidity look-through) rather than stress →
  `portfolio-exposure-analyzer`.
- Counterparty/settlement/collateral limit monitoring across counterparties →
  `counterparty-exposure-monitor`.

## Adjacent-skill handoffs
See [references/handoffs.md](references/handoffs.md). This skill emits a liquidity-stress pack
with a durable `analysis_id`; downstream drafting/monitoring skills and human committees
consume it. It must not duplicate their determination, drafting, or action steps.

## Inputs and prerequisites
- **Portfolio identifier**, `as_of` date, `config_version`, `base_currency`, and portfolio
  **NAV**.
- **Positions** — each with `market_value`, `adv_value` (traded value/day), `spread_bps`,
  `asset_class`, and a `source_ref`. Schema: [scripts/validate_input.py](scripts/validate_input.py).
- A **scenario** object with transparent assumptions: `adv_haircut`, `spread_multiple`,
  `price_shock`, `redemption_pct`, `redemption_notice_days`. Baseline = no stress.
- Optional **collateral** block: liquidity `buffer` and `margin_positions[]` (notional +
  source_ref) for the margin/collateral test.
- Read access to PMS/OMS, market-data, and risk systems; approved thresholds/config (see
  [references/domain-rules.md](references/domain-rules.md)).

## Source hierarchy
See [references/source-map.md](references/source-map.md). PMS/OMS holdings are the position of
record; market-data supplies ADV, spread, and price; the versioned liquidity config supplies
thresholds; the scenario supplies stress assumptions. Cite every breached metric's evidence
to a source position row, and record the config version and scenario assumptions used.

## Workflow
1. **Scope & scenario** — confirm the portfolio, `as_of`, and the scenario assumptions;
   validate with `validate_input`. Never infer stress parameters silently.
2. **Compute metrics (deterministic)** — run
   [scripts/calculate_or_transform.py](scripts/calculate_or_transform.py) to build the
   liquidation profile (participation-of-ADV model) and the metrics: redemption coverage,
   full-liquidation horizon, collateral-buffer coverage, liquidation cost, and illiquid
   concentration. Each breached metric returns its evidence rows and the basis behind it.
   Metrics are **explainable**, not a black-box score.
3. **Assemble evidence** — for each breached metric, attach the specific positions and the
   basis it deviates from, with citations.
4. **Suggest band** — map the breached-metric set to a band (Adequate / Watch / Stressed)
   per the configured, documented mapping. This is a triage suggestion for a human committee,
   explicitly **not** a decision to gate, suspend, or trade.
5. **Write the pack** — plain-language explanation per metric + the evidence + the scenario
   assumptions + the suggested band + explicit modeling caveats to weigh.

## Validation loop
Run `validate_input` before and [scripts/validate_output.py](scripts/validate_output.py)
after. The output check confirms: every breached metric has evidence + citation; the band
maps deterministically from the breached set; scenario assumptions are recorded; no
recommendation/action/breach-determination language is present; the standing disclaimer is
present; and modeling caveats are included. Fail closed on any miss.

## Human approval
`external-delivery`: human review required before the pack is sent outside the analytics team
or written to a case/system of record. No approval is needed for the analyst's own read. The
skill never places a trade, gates redemptions, or takes any fund-liquidity action.

## Failure handling
- **Thin/absent market data** (missing ADV or spread) → compute only the metrics the data
  supports; label the rest "not evaluable"; do not fabricate liquidity.
- **`adv_value <= 0`** → treat the position as beyond the max horizon (illiquid); never assume
  it can be sold.
- **No redemption modeled** (`redemption_pct` 0) → redemption coverage is not evaluable; say so.
- **No margin positions** → collateral-buffer coverage is not evaluable; say so.
- **NAV vs. summed market value mismatch** → warn (unmodeled cash/other); report coverage
  relative to NAV and flag the gap.
- **Ambiguous portfolio/scenario** → stop and confirm; never analyze the wrong book or an
  unstated scenario.
- **Tool timeout** → return partial metrics computed so far with a clear "incomplete" flag.

## Output contract
1. **Summary** — portfolio, `as_of`, scenario name, NAV, count of breached metrics, suggested band.
2. **Liquidity profile** — value liquidatable by horizon bucket (1/7/30d), full-liquidation
   days, portfolio liquidation cost (bps + currency).
3. **Metrics** — per metric: name, value, threshold, breached flag, plain-language reason,
   evidence rows (cited), and the basis it deviates from.
4. **Scenario assumptions** — the exact adv_haircut, spread_multiple, price_shock,
   redemption_pct, notice days, and participation rate used (transparency is mandatory).
5. **Caveats** — explicit modeling limitations (ADV is an estimate, correlated redemptions,
   second-order impact) so the committee weighs both sides.
6. **Data gaps / not-evaluable metrics.**
7. **Machine-readable** — metrics + evidence + `analysis_id` for downstream skills.
8. **Standing disclaimer** — "Liquidity analysis and evidence only under stated scenario
   assumptions; not an investment, trading, or fund-liquidity-action determination. No trade,
   redemption gate, or other liquidity action has been taken."
See [references/controls.md](references/controls.md).

## Privacy and records
MNPI / client-confidential holdings. Minimize position data in output to what evidences a
breached metric; do not expose full holdings when a summary suffices. Retain the analysis +
citations + config version + scenario per records policy; log the read and any
external-delivery approval. Never exfiltrate holdings or client data.

## Gotchas
- **A metric is not a decision.** A Stressed band justifies *committee review*, never an
  autonomous gate, suspension, side pocket, trade, or breach finding.
- **Scenarios are assumptions, not forecasts.** Always record the parameters and invite the
  reviewer to vary them; a single scenario is not a verdict on the fund's liquidity.
- **ADV is fragile under stress.** Liquidity dries up exactly when you need it; the
  `adv_haircut` exists for this — do not present baseline ADV as reliable in a crisis.
- **Coverage is relative to NAV and the notice window.** State both; a comfortable 30-day
  number can hide a 1-day shortfall.
- **Do not tune thresholds to a desired answer.** Thresholds come from the approved versioned
  config, not from what makes the book look liquid.
- **Breach language is a determination.** Describe metrics factually ("coverage 0.80 vs 1.0
  threshold"); never assert the fund "is in breach" or "is illiquid" — that is for compliance
  and the committee.
