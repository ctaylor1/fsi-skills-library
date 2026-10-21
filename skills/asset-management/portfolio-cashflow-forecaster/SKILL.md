---
name: portfolio-cashflow-forecaster
description: >-
  Build a deterministic, source-linked liquidity cash-flow forecast: aggregate a fund's
  subscriptions, redemptions, coupons, dividends, maturities, collateral, and known funding
  needs into dated buckets, roll opening cash forward under each ANALYST-SUPPLIED scenario, and
  emit a dated liquidity ladder (net flow, closing balance, any shortfall bucket) with formula
  tie-outs, a provenance-tagged assumptions log, and
  optional reconciliation to an approved-engine total. Use when a liquidity-risk analyst asks to
  forecast the fund's cash ladder, project liquidity under supplied scenarios, or aggregate
  flows and funding needs into a dated, reproducible forecast with an assumptions log. HARD
  BOUNDARY: it NEVER chooses or recommends a scenario, recommends or executes selling or
  liquidating any asset, sets or recommends a liquidity buffer, or gives investment advice;
  stressed-liquidation / liquidation-horizon analysis is handed off to fund-liquidity-assessor
  (distinct from liquidity-risk-scenario-analyzer).
license: MIT
compatibility: Amazon Quick Desktop; requires PMS/OMS, transfer-agent, custodian, collateral-management, market-data, and versioned liquidity-config MCP integrations (all read-only).
metadata:
  aws-fsi-category: "Asset Management"
  aws-fsi-skill-type: "Artifact-creation skills"
  aws-fsi-risk-tier: "R2"
  aws-fsi-archetype: "Model & calculate"
  aws-fsi-agent-pattern: "Interactive production copilot"
  aws-fsi-delivery-wave: "Wave 5 - 2026 industry expansion"
  aws-fsi-action-mode: "Draft-only; no system-of-record change"
  aws-fsi-scheduled-agent: "no"
  aws-fsi-baseline-status: "existing-updated"
  aws-fsi-human-approval: "external-delivery"
  aws-fsi-data-classification: "Highly Confidential (MNPI / client-confidential)"
  aws-fsi-jurisdictions: "US (default); configure additional jurisdiction packs per deployment"
  aws-fsi-owner: "Asset Management investment & product"
  aws-fsi-primary-user: "Liquidity-risk analyst"
  aws-fsi-version: "0.2.0"
  aws-fsi-recertification-date: "2027-09-20"
---

# Portfolio Cash-flow Liquidity Forecaster

## Purpose and outcome
Given a portfolio's or fund's opening cash, a set of **dated, sourced cash flows**
(subscriptions, redemptions, coupons, dividends, maturities, collateral, and known funding
needs), a set of **dated horizon buckets**, and a set of **analyst-supplied scenarios**, build
a **deterministic, source-linked liquidity forecast**: bucket each flow, apply each scenario's
documented category multipliers and date shifts, and roll the opening balance forward into a
dated projected-liquidity ladder — per bucket net flow, closing balance, cumulative net, and
the earliest projected-shortfall bucket if any. Every scenario ties out; every input is logged
with provenance and a citation; the forecast is reproducible from a hash of its inputs and can
reconcile to an approved-engine total. A successful output lets a liquidity-risk analyst show
*what the cash position looks like under stated assumptions* and hands a reproducible forecast
(`forecast_id`) to review, committee, and stressed-liquidation skills. The **scenario choice,
any cash-raising or asset-sale decision, and any liquidity-buffer level stay with a human.**

## Use when
- "Forecast the fund's cash ladder / liquidity over the next weeks under my scenarios."
- "Aggregate our subscriptions, redemptions, coupons, dividends, maturities, collateral, and
  known funding needs into a dated forecast."
- "Roll opening cash forward by bucket and show me the closing balance and any shortfall bucket."
- "Give me the dated forecast plus the assumptions log with sources for every cash flow."
- A liquidity-risk analyst needs a reproducible, tied-out cash-flow forecast to anchor a
  liquidity review.

## Do not use
- The user wants the skill to **choose or recommend a scenario**, **decide to raise cash / sell
  or liquidate assets**, or **set / recommend a liquidity buffer** ("which scenario should we
  plan around?", "what should we sell?", "set the buffer") → out of scope (prohibited); build
  the forecast and route the judgment to the liquidity-risk analyst and the liquidity risk
  committee (see [references/handoffs.md](references/handoffs.md)).
- **Stressed-liquidation analysis** — liquidation horizons, market-impact/cost, redemption
  coverage under an ADV-participation model → `fund-liquidity-assessor`.
- **Institution-wide treasury / ALM survival-horizon** stress (bank funding, LCR-style
  regulatory scenarios, contingency-funding actions) → `liquidity-risk-scenario-analyzer`
  (a distinct R3 skill; do not conflate it with `fund-liquidity-assessor`).
- **Mandate / guideline / regulatory liquidity-bucket breach determinations** →
  `investment-mandate-reviewer` plus human compliance sign-off.
- **Personalized investment, trading, or tax advice** → licensed-human matter.

## Adjacent-skill handoffs
See [references/handoffs.md](references/handoffs.md). This skill emits a dated liquidity forecast
with a durable `forecast_id`, `inputs_hash`, and `config_version`; downstream review, committee,
and stressed-liquidation skills consume it without rebuilding it. It must not duplicate their
determination, stress-modeling, drafting, or action steps.

## Inputs and prerequisites
- **Portfolio/fund identifier**, `as_of` date, `forecast_start` date, `config_version`,
  `currency`, and `units`.
- **Opening cash** at `forecast_start` as `{value, provenance, citation}`.
- **Bucket dates** — an ascending, non-empty list of period-end dates defining the horizon.
- **Cash flows** — each with `id`, `category` (one of subscription, redemption, coupon,
  dividend, maturity, collateral, funding_need), `date`, positive `amount` (magnitude),
  optional `direction` (required for `collateral`), and `{provenance, citation}`.
- **Scenarios** — an object keyed by name (a `base` scenario is **required**); each carries
  `{provenance, citation}`, a `category_multipliers` map, an optional `category_date_shift_days`
  map, and an optional `approved_engine_net` (+ `approved_engine_source`) to reconcile against.
  Schema: [scripts/validate_input.py](scripts/validate_input.py).
- Read access to PMS/OMS, transfer-agent, custodian, collateral-management, and market-data
  systems, plus the versioned liquidity config (see [references/source-map.md](references/source-map.md)).

## Source hierarchy
See [references/source-map.md](references/source-map.md). The transfer agent is the anchor for
subscription/redemption flows; the custodian/PMS for coupons, dividends, maturities, and the
cash balance; collateral-management for margin/collateral; the operations calendar for known
funding needs; and the analyst for the scenarios. **Cite every cash flow and every scenario
with a date**; a confirmed/settled figure outranks an estimate, and conflicts are recorded as
explicit sourced overrides — the skill never invents a cash flow or a scenario.

## Workflow
1. **Scope & scenarios** — confirm the portfolio, `as_of`, `forecast_start`, currency/units,
   the bucket dates, and the analyst-supplied scenarios; load the sourced cash flows. Never
   infer or select a scenario.
2. **Validate input** — run [scripts/validate_input.py](scripts/validate_input.py); resolve
   errors (unknown category, non-positive amount, collateral without direction, non-ascending
   buckets, missing `base` scenario), note warnings (missing provenance, out-of-horizon flows).
3. **Build the forecast (deterministic)** — run
   [scripts/calculate_or_transform.py](scripts/calculate_or_transform.py): bucket each flow,
   apply each scenario's multipliers/date shifts, and roll the opening balance forward into the
   dated ladder with per-scenario tie-outs, an assumptions log, and any reconciliation.
4. **Read the checks** — confirm every tie-out passes, each reconciliation ties, and every
   assumption is logged with provenance + citation. A projected-shortfall bucket is a **factual
   signal**, not a decision.
5. **Write the pack** — a plain-language narrative of the opening position, the buckets, each
   scenario's closing-balance path, and any projected shortfall, with the assumptions log, the
   scenario parameters, and the standing disclaimer. No scenario choice, sale, or buffer.

## Validation loop
Run `validate_input` before and [scripts/validate_output.py](scripts/validate_output.py) after.
The output check independently re-derives the tie-outs (category aggregation; `net_flow ==
inflows - outflows`; `closing == opening + net`; balance continuity; cumulative net; totals and
by-category), confirms each reconciliation ties, requires a `base` scenario, requires provenance
+ citation on every assumptions-log entry and `forecast_id` + `inputs_hash`, screens the
narrative for scenario-choice / asset-sale / buffer-setting / advice language, and requires the
disclaimer. **Fail closed on any miss.**

## Human approval
`external-delivery`: human review and approval are required before the forecast is delivered to a
liquidity risk committee, board, client, or data room, or written to any system of record. No
approval is needed for the analyst's own read. The skill takes **no liquidity action** and makes
**no scenario, sale, or buffer decision.**

## Failure handling
- **Unknown category / non-positive amount / collateral without direction** → `validate_input`
  errors; do not guess a category or a sign.
- **Missing `base` scenario / non-ascending bucket dates** → error; the horizon and the base
  case are required.
- **Unsourced cash flow or scenario** → warned on input, **rejected** on output; every input
  needs a source.
- **Reconciliation mismatch** (computed net != approved-engine net) → fail closed; do not
  present the forecast as reconciled.
- **Cash flow dated before `forecast_start` or beyond the last bucket** → excluded and listed
  in `excluded_beyond_horizon`; never silently dropped.
- **Ambiguous portfolio/scenario** → stop and confirm; never forecast the wrong book or an
  unstated scenario.
- **Tool timeout** → return the scenarios computed so far with an explicit "incomplete" flag.

## Output contract
1. **Summary** — portfolio (masked as needed), `as_of`, `forecast_start`, currency/units,
   opening cash, bucket dates, scenario names, and each scenario's minimum closing balance and
   first projected-shortfall bucket (if any).
2. **Forecast ladder** — per scenario, per bucket: opening balance, inflows and outflows by
   category, net flow, closing balance, and cumulative net.
3. **Scenario parameters** — the exact category multipliers and date shifts applied (transparency
   is mandatory; the analyst supplied them).
4. **Assumptions log** — opening cash, every cash flow, and every scenario with `provenance` +
   `citation`.
5. **Model checks** — the tie-out results, each reconciliation, and `base_present`.
6. **Machine-readable** — the full forecast JSON with `forecast_id`, `inputs_hash`, and
   `config_version` for downstream skills.
7. **Standing disclaimer** — "Illustrative liquidity cash-flow forecast for analytical purposes
   only, computed from analyst-supplied cash flows and scenarios; it does not choose or
   recommend a scenario, recommend or execute the sale or liquidation of any asset, set or
   recommend a liquidity buffer, or provide investment advice. A projected shortfall is a signal
   for human review, not a decision or instruction; outputs depend entirely on the stated
   assumptions, which a qualified human must review."
See [references/controls.md](references/controls.md) and
[references/domain-rules.md](references/domain-rules.md).

## Privacy and records
MNPI / client-confidential. Fund flows and holdings frequently embed material non-public
information (large redemptions, deal-driven funding needs) — treat the forecast, its inputs, and
`forecast_id` as need-to-know and respect information barriers. Minimize position/flow data in
output to what evidences the forecast. Retain the forecast, its assumptions log, and
`config_version` per records policy; log the read and any external-delivery approval. Never
exfiltrate fund or client data.

## Gotchas
- **A forecast is not a decision.** A projected closing balance or shortfall is conditional on
  the analyst-supplied cash flows and scenarios; it is never a scenario choice, a sell/raise-cash
  instruction, or a buffer level.
- **The skill never picks the scenario.** Scenarios, multipliers, and date shifts are supplied
  by the analyst and logged; the skill computes each one and chooses none.
- **Magnitudes are positive; direction carries the sign.** Redemptions and funding needs are
  outflows; collateral must state `post` (outflow) vs `return` (inflow) explicitly.
- **Coverage is relative to the bucket dates.** A comfortable month-end balance can hide an
  intra-month shortfall in an earlier bucket; state the bucket where the minimum occurs.
- **Reconcile, do not tune.** When an approved-engine total is supplied, the forecast must tie
  to it; never bend a cash flow or multiplier to reach a wanted number.
- **Out-of-horizon flows are excluded, not dropped.** Anything before `forecast_start` or after
  the last bucket is listed in `excluded_beyond_horizon` so the omission is auditable.

## Phase 1 executable boundary

Read [the bounded offline contract](references/phase1-contract.md) before running the scripts or relying on a handoff. It states required input evidence, unavailable cases and source-bound validation. Enterprise connectors and review queues described above are deployment interfaces, not implemented integrations.

## Phase 1 support boundary

Supplied dated flows and scenario ladder; uncertain commitment pacing not implemented

This package performs only its documented local supplied-input operations. Live source access, authenticated permissions, production engines and professional acceptance are separate deployment requirements. Generated resources are pinned in `references/package-manifest.json`; maintain the canonical shared source. Legacy identifiers resolve through the repository migration registry.
