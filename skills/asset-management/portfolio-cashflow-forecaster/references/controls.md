# Controls — portfolio-cashflow-forecaster

- **Risk tier:** R2 — analytical / drafting support. **Action mode:** Draft-only; no
  system-of-record change.
- **Human approval:** `external-delivery` — required before the forecast is delivered to a
  liquidity risk committee, board, client, or data room, or otherwise written to a system of
  record.

## Prohibited (fail closed)

- No **scenario choice or recommendation** — the skill computes every analyst-supplied scenario
  and never says which one to plan around, which is "most likely", or which is "recommended".
- No **asset-sale / liquidation / cash-raising recommendation or instruction** ("sell the
  high-yield book", "raise $X by selling", "liquidate positions") — those are portfolio-manager /
  dealing-desk / authorized-system actions.
- No **liquidity-buffer setting or recommendation** ("set the buffer to X", "the buffer should
  be", "hold X in cash") — buffer policy is a human/committee decision.
- No **redemption gating, suspension, or side-pocket activation** — authorized fund actions.
- No **guarantee** that liquidity will cover redemptions or that a scenario will occur.
- No **personalized investment, trading, or tax advice**.
- No **cash flow or scenario without provenance**; no cash flow, multiplier, or tolerance bent to
  reach a wanted forecast.

## Required output screens (`scripts/validate_output.py`)

- Every scenario ties out, re-derived independently: per bucket `inflows ==
  sum(inflow_by_category)` and `outflows == sum(outflow_by_category)`; `net_flow == inflows -
  outflows`; `closing == opening + net_flow`; balance continuity (`opening == prior closing`,
  first `opening == opening_cash`); `cumulative_net` is the running sum; `totals.net_over_horizon
  == sum(bucket net_flow) == sum(totals.by_category)`.
- `first_shortfall_bucket` and `min_closing_balance` are internally consistent with the ladder.
- A **`base` scenario is present** (the analyst supplies every scenario).
- Any scenario carrying an **approved-engine total reconciles** (`computed_net == approved_engine_net`
  within tolerance); mismatch fails closed.
- Every `assumptions_log` entry has a non-empty `provenance` **and** `citation`.
- `forecast_id` and `inputs_hash` present (reproducibility).
- No scenario-choice / asset-sale / buffer-setting / advice / guarantee language in the author
  narrative (regex screen; the standing disclaimer is stripped first so it cannot self-trip).
- Standing disclaimer present.

## Data classification, privacy, records

- **Highly Confidential (MNPI / client-confidential).** Fund flows often embed material
  non-public information (large redemptions, deal-driven funding needs). Treat the forecast, its
  inputs, and its `forecast_id` as need-to-know.
- Respect information barriers; do not move MNPI across a public-side / wall.
- Minimize flow/position data in output to what evidences the forecast.
- Retain the forecast, its assumptions log, and `config_version` per records policy; log the read
  and any external-delivery approval.

## Reproducibility & change control

`inputs_hash` binds the forecast to the exact numeric inputs; the `config_version` binds the
category set, bucket conventions, tolerance, and reconciliation targets. Re-running the same
inputs and config reproduces the same `forecast_id` and the same ladder. Changing an input
changes the hash — the audit trail shows what moved.

## Separation of duties

Building the forecast (this skill) is separate from independently reviewing it, from choosing a
scenario, and from any liquidity action (raising cash, selling assets, setting a buffer, gating
redemptions). The forecast is a draft input to a human's judgment, never a substitute for it.
