# Domain Rules — transaction-cost-estimator

Deterministic implementation-shortfall TCA. The firm's approved, versioned methodology
governs coefficients and models; nothing is invented per order.

## Cost components (basis points of arrival price, signed by side)
Let `s = +1` for a buy, `-1` for a sell; `arr` = arrival price.

| Component | Formula (bps) | Notes |
| --------- | ------------- | ----- |
| `half_spread` | `spread_bps / 2` | From methodology config |
| `commission` | `commission_bps` | Explicit fees/commissions |
| `market_impact` | `impact_coef * volatility * sqrt(exec_qty / adv) * 10000` | Square-root impact model; volatility as a daily fraction |
| `delay` | `s * (arrival_price - decision_price) / arr * 10000` | Implementation shortfall from decision to arrival (0 if no decision price) |
| `realized` | `s * (exec_price - arrival_price) / arr * 10000` | Execution vs arrival |
| `opportunity` | `s * (unfilled_qty / order_qty) * (close_price - arrival_price) / arr * 10000` | Cost of unfilled quantity vs close |

`total_bps = half_spread + commission + market_impact + delay + realized + opportunity`.
Currency: `component_ccy = component_bps / 10000 * notional`, `notional = exec_qty * arr`.

## Uncertainty
`market_impact` carries a band `± impact_uncertainty_pct` (config, default 25%). The output
reports a `total_bps` range from the impact band. A point estimate without a band is invalid.

## Rules / hard boundaries (fail closed)
- Never route/execute/amend; never select/recommend a venue/broker/algo; never assert best
  execution.
- Missing ADV/volatility/benchmark → the dependent component is `not_evaluable`, not guessed.
- Guard division: `adv > 0` and `arr > 0` required for the dependent components.
- Sign every price-difference component by side `s`.
