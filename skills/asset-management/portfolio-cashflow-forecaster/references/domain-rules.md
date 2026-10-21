# Domain Rules — portfolio-cashflow-forecaster

The deterministic cash-flow aggregation, the bucketing, the scenario construction, and the
tie-outs. The category set, bucket conventions, tolerance, and reconciliation targets are
**configuration** (versioned, owned by the liquidity-risk / product-governance function), not the
skill's judgment, and are never bent to reach a desired forecast. Orientation: a standard dated
liquidity / cash-ladder projection as used in fund liquidity-risk management; the firm's liquidity
standard takes precedence where it differs.

## Cash-flow categories and direction

| Category | Default direction | Notes |
| -------- | ----------------- | ----- |
| `subscription` | inflow | Investor subscriptions |
| `coupon` | inflow | Fixed-income coupons |
| `dividend` | inflow | Equity dividends |
| `maturity` | inflow | Principal returned at maturity |
| `redemption` | outflow | Investor redemptions |
| `funding_need` | outflow | Known settlements, capital calls, fees, expenses |
| `collateral` | **explicit** | Margin call = `outflow` (post collateral); collateral return = `inflow` |

**Amounts are positive magnitudes; the direction carries the sign.** A `collateral` flow has no
default direction and must state one; `validate_input` fails closed if it does not.

## Bucketing (per scenario, in `scripts/calculate_or_transform.py`)

- `bucket_dates` is an ascending, non-empty list of **period-end dates** defining the horizon.
- Each cash flow's (optionally shifted) date `d` is assigned to the **first bucket whose end-date
  `>= d`**. A flow dated before `forecast_start`, or after the last bucket, is **excluded** and
  listed in `excluded_beyond_horizon` (never silently dropped).

## Scenario application (analyst-supplied; the skill chooses none)

For each scenario, per category:

```
magnitude   = amount * category_multipliers.get(category, 1.0)
effective_d = flow_date + timedelta(days = category_date_shift_days.get(category, 0))
```

A `base` scenario is **required**; typically its multipliers are identity (`1.0`). Every scenario
carries its own `provenance` + `citation` (it is the analyst's assumption). The skill applies each
scenario deterministically and never selects, ranks, or recommends one.

## Ladder roll-forward (per scenario, per bucket `i`)

```
inflows_i   = sum(inflow magnitudes assigned to bucket i, by category)
outflows_i  = sum(outflow magnitudes assigned to bucket i, by category)
net_flow_i  = inflows_i - outflows_i
opening_1   = opening_cash
opening_i   = closing_{i-1}
closing_i   = opening_i + net_flow_i
cumulative_net_i = cumulative_net_{i-1} + net_flow_i
```

Reported per scenario: the ladder, `totals` (inflows, outflows, `net_over_horizon`, signed
`by_category`), `min_closing_balance` (+ bucket), and `first_shortfall_bucket` (the earliest bucket
with `closing < 0`, or `null`). A shortfall bucket is a **factual signal for human review**, not a
decision, a sell instruction, or a buffer.

## Reconciliation to an approved-engine total (optional)

If a scenario supplies `approved_engine_net` (e.g. a treasury cash-ladder engine's expected net),
the engine emits `reconciliation = {approved_engine_net, computed_net, difference, source,
matches}`. `matches` is `true` only when `|computed_net - approved_engine_net| <= tolerance`.
`validate_output` **fails closed** on a mismatch; the target is never invented and the forecast is
never tuned to hit it.

## Tie-outs (every one must hold within tolerance; re-checked in validate_output)

1. per bucket: `inflows == sum(inflow_by_category)` and `outflows == sum(outflow_by_category)`
2. per bucket: `net_flow == inflows - outflows`
3. per bucket: `closing == opening + net_flow`, with balance continuity across buckets
4. `cumulative_net` is the running sum; `cumulative_net[last] == closing[last] - opening_cash`
5. `totals.net_over_horizon == sum(bucket net_flow) == sum(totals.by_category)`
6. `first_shortfall_bucket` / `min_closing_balance` consistent with the ladder
7. any supplied `approved_engine_net` reconciles

## Assumption provenance (mandatory)

Every input — opening cash, each cash flow, and each scenario — is recorded in the
`assumptions_log` with a `provenance` class and a dated `citation`. An entry missing either is a
control failure — `validate_output` rejects the pack.

## Reproducibility

`forecast_id = pclf-{portfolio_id}-{as_of}-{inputs_hash}`, where `inputs_hash` is a SHA-256 over
the normalized numeric inputs (opening cash, forecast start, bucket dates, cash flows, scenario
parameters, reconciliation targets). Identical inputs reproduce the identical forecast and numbers.

## Hard boundaries (fail closed)

- Never **choose, rank, or recommend a scenario**; compute every analyst-supplied scenario and
  select none.
- Never recommend or execute the **sale or liquidation of any asset**, or a cash-raising action.
- Never **set or recommend a liquidity buffer**, gate/suspend redemptions, or activate a side pocket.
- Never **guarantee** that liquidity covers redemptions or that a scenario will occur.
- Never fabricate or leave unsourced a cash flow or scenario; every input carries provenance.
- Never bend a cash flow, multiplier, tolerance, or reconciliation target to reach a wanted forecast.
- Stressed-liquidation modeling belongs to `fund-liquidity-assessor`; institution-wide
  treasury/ALM survival-horizon stress belongs to `liquidity-risk-scenario-analyzer`.
