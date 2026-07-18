# Domain Rules — portfolio-exposure-analyzer

Exposure **dimensions**, how look-through is applied, and how a documented **concentration
limit** screen maps to a **review-priority band**. Limits are configuration (versioned,
owned by the risk/investment-guidelines team), not hard-coded judgments, and are never
tuned to a specific portfolio. The firm's investment-guidelines standard and the fund's
IMA/prospectus take precedence over the defaults below.

## Exposure dimensions

| Dimension | Aggregated as | Notes |
| --------- | ------------- | ----- |
| `issuer` | Net market value per issuer, **look-through applied** | Sovereign/cash asset classes exempt from the issuer limit (config) |
| `sector` | Net market value per GICS-style sector | Government/cash exempt from the sector limit (config) |
| `country` | Net market value per country of risk | Home/base country exempt from the country limit (config) |
| `currency` | Net market value per currency; plus **total non-base** aggregate | Screen is on total non-base-currency exposure |
| `asset_class` | Net market value per asset class | Reported; no default limit |
| `duration` | Fixed-income **sleeve** modified duration + portfolio duration contribution | Screened vs a target ± tolerance band |
| `liquidity` | Days-to-liquidate buckets; `illiquid_pct` = share beyond the horizon | Screened vs an illiquid-share limit |
| `factor` | Weighted net factor exposure | **Evaluable only if positions carry `factors` loadings** (factor-model service); otherwise `not_evaluable` |

Market values are provided already converted to the base currency by the market-data
service. Every exposure bucket keeps the contributing positions and their citations.

## Look-through

A pooled vehicle (fund/ETF/derivative) with a `look_through` constituent list is
**decomposed**: each constituent's `weight × position_market_value` is attributed to the
constituent's issuer/sector/country/currency. The vehicle itself is **not** double-counted
into those dimensions (it still counts as its own `asset_class` and carries its own
liquidity horizon). A vehicle with no look-through data is attributed to itself as a single
issuer — state this limitation in the output.

## Concentration limits (default config; versioned)

| Key | Default | Screen |
| --- | ------- | ------ |
| `single_issuer_max_pct` | 5.0 | issuer exposure > soft limit → `over_soft` finding |
| `single_issuer_hard_pct` | 10.0 | issuer exposure > hard limit → `over_hard` finding (escalator) |
| `sector_max_pct` | 25.0 | sector exposure > limit → finding |
| `country_max_pct` | 40.0 | country (non-home) exposure > limit → finding |
| `non_base_currency_max_pct` | 30.0 | total non-base exposure > limit → finding |
| `illiquid_max_pct` / `illiquid_horizon_days` | 20.0 / 7 | share beyond horizon > limit → finding (escalator) |
| `duration_target` / `duration_tolerance` | 6.5 / 1.5 | sleeve duration outside band → finding |
| `home_country` | US | excluded from the country screen |
| `issuer_sector_exempt_asset_classes` | govt_bond, cash | excluded from issuer/sector screens |

A finding is a **factual statement** that an exposure exceeds a *documented limit*. It is
**not** a mandate-compliance determination — that adjudication belongs to
`mandate-compliance-monitor` and a human. Comparisons are strict `>` (an exposure exactly at
the limit is at-limit, not over).

## Priority mapping (deterministic, documented)

| Suggested band | Rule |
| -------------- | ---- |
| **Informational** | 0 findings — all exposures within documented limits |
| **Review** | 1–2 findings, none an escalator |
| **Elevated** | ≥ 3 findings, OR any `over_hard` issuer finding, OR any `liquidity` finding |

Escalators = any `over_hard` issuer finding or any liquidity finding. The band is a **triage
suggestion for a human reviewer**; it never triggers a trade, a rebalance, or a compliance
finding. The same mapping is enforced in `scripts/validate_output.py`.

## Hard boundaries (fail closed)

- Never state or imply the portfolio **is in breach of**, **violates**, or is
  **non-compliant** with a mandate, guideline, or limit — describe the exposure factually
  ("exposure X% exceeds the documented limit of Y%") and attribute adjudication to the human
  and `mandate-compliance-monitor`.
- Never recommend, stage, or execute a **trade, rebalance, hedge, or divestment** to cure an
  exposure.
- Never give **personalized investment, tax, or legal advice** ("you should buy/sell/trim").
- Never tune limits to the portfolio or infer "what's appropriate for this fund" beyond the
  versioned config.

## Considerations to weigh (always include when findings fired)

Benchmark-driven weights (active vs absolute exposure differ), an intended mandate-permitted
tilt or thematic sleeve, stale or partial look-through data, FX/duration overlays not in the
holdings file, a documented private-assets/illiquid bucket allowance, and the sovereign/cash
exemptions. The pack must invite the reviewer to weigh these before drawing any conclusion.
