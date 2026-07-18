# Source Map — portfolio-exposure-analyzer

## Source hierarchy (highest first)

| Rank | Source (MCP integration) | Used for | Access |
| ---- | ------------------------ | -------- | ------ |
| 1 | **PMS/OMS holdings** (position of record) | Positions, market values, weights, IDs | Read-only |
| 2 | **Market & reference data** | Prices, FX to base currency, issuer/sector/country/currency classification, ratings, duration | Read-only |
| 3 | **Look-through / fund-constituent** data | Decomposing pooled vehicles to underlying issuers | Read-only |
| 4 | **Risk / factor model** | Modified duration, factor loadings, liquidity estimates | Read-only |
| 5 | **Investment-guidelines config** (versioned) | Concentration limits, exemptions, priority mapping | Read-only |

Positions arrive with `market_value` **already converted to `base_currency`** by the
market-data service; this skill does not perform FX conversion. The PMS/OMS holdings file is
the position of record — never substitute a research note, a fact-sheet figure, or an analyst
estimate for a holding. If holdings and a downstream report conflict, cite both and flag for
the reviewer.

## Citation format

`pms:{source_ref}@{as_of}` — e.g. `pms:pf=PF-AM-1007;pos=P-1@2026-07-16`. Look-through
attribution cites the vehicle and the constituent:
`pms:pf=PF-AM-1007;pos=P-8#lt=Hansol Electronics@2026-07-16`. Every exposure bucket and every
finding cites the specific contributing rows.

## Freshness / effective dates

- Limits config is a **versioned contract**; the output records `config_version` so an
  analysis is reproducible.
- Holdings, prices, FX, and look-through constituents each have an as-of date; state the
  effective `as_of` in the output and flag any stale constituent data.
- Look-through decomposition is only as current as the fund's last published holdings — note
  the constituent data date when it lags `as_of`.

## Least-privilege operations (deployment)

- `pms.holdings(portfolio_id, as_of)` → positions with market value in base currency.
- `marketdata.classify(instrument_id)` → issuer, sector, country, currency, rating.
- `marketdata.fx(as_of)` → rates used upstream to convert to base (recorded, not applied here).
- `lookthrough.constituents(instrument_id, as_of)` → fund/derivative decomposition + weights.
- `riskmodel.metrics(instrument_id)` → modified duration, factor loadings, liquidity days.
- `config.get('exposure', version)` → limits, exemptions, priority mapping.

All read-only, deterministic, durable `exposure_id`, below the fixed timeout; page large
portfolios and look-through trees as resumable stages. No write, order, or execution
operations are bound by this skill.
