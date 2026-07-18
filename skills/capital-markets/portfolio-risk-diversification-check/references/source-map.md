# Source Map — portfolio-risk-diversification-check

## Source hierarchy (highest first)

| Rank | Source (MCP integration) | Used for | Access |
| ---- | ------------------------ | -------- | ------ |
| 1 | **Book of record / custody positions** (position of record) | Holdings, weights, asset class | Read-only |
| 2 | **Market & reference data** | Sector/region/asset-class classification, factor loadings, correlation matrix, liquidity estimates | Read-only |
| 3 | **OMS/EMS** (optional) | Intended/target weights when analyzing a proposed vs. current book | Read-only |
| 4 | Risk-analytics **config** (versioned) | Concentration thresholds and band mapping | Read-only |

The position/custody record is authoritative for **what is held and in what weight**.
Classification, factor, correlation, and liquidity inputs come from the market/reference-data
service and are **model inputs**, not ground truth — a name may map to different sector or
region buckets under different taxonomies. Never substitute an investor's assertion of what
they "really" hold for the position record; if a statement and the position record conflict,
cite both and flag it.

## Citation format

`{system}:{ref}@{date}` — e.g. `positions:pf=****3021;sym=AAPL@2026-07-15`,
`corr:pf=****3021;pair=AAPL-MSFT@2026-07-15`. Every flagged check cites the specific
positions, sector/region bucket, factor, or correlation pair behind it and the `as_of` date.

## Freshness / effective dates

- Config (thresholds, band mapping) is a **versioned contract**; the output records the
  `config_version` used so an analysis is reproducible.
- Prices, weights, correlations, and factor loadings all carry an `as_of`; the output states
  the exact `as_of` and warns when inputs are stale or drawn from different dates.
- Correlations and factor loadings are window-dependent estimates; the profile states this and
  does not present them as fixed properties of the holdings.

## Least-privilege operations (deployment)

- `positions.read(portfolio_id, as_of)` → bounded holdings with weights.
- `refdata.classify(symbols)` → sector/region/asset-class buckets.
- `refdata.factors(symbols, as_of)` → factor loadings.
- `refdata.correlations(symbols, window)` → correlation matrix.
- `refdata.liquidity(symbols, as_of)` → days-to-liquidate estimates.
- `config.get('portfolio-risk', version)` → thresholds + band mapping.

All read-only, deterministic, below the fixed timeout, with a durable `analysis_id`; page
large books as resumable stages. No order, trade, or write operation is bound by this skill.
