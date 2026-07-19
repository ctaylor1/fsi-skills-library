# Source Map — liquidity-risk-scenario-analyzer

## Source hierarchy (highest first)

| Rank | Source (MCP integration) | Used for | Access |
| ---- | ------------------------ | -------- | ------ |
| 1 | Treasury / **ALM** position of record | Cash-flow items, funding maturities, deposit balances by bucket | Read-only |
| 2 | **Collateral / HQLA inventory** | Counterbalancing assets, asset class, market value, base haircut | Read-only |
| 3 | **Core-banking deposits & funding** | Deposit categorization (stable/less-stable/operational), wholesale funding | Read-only |
| 4 | **Market data** | Prices/haircuts underpinning collateral valuation and stressed add-ons | Read-only |
| 5 | ALM/ERM **scenario & limit config** (versioned) | Stress rates (runoff/rollover/inflow), CBC haircut add-ons, limits | Read-only |

Never substitute an ad-hoc assumption for the position of record or the versioned config. If the
ALM position and a downstream extract conflict, cite both and flag for the analyst.

## Citation format

`liq:{ref}@{as_of}` — e.g. `liq:entity=LE-BANK-01;scenario=COMBINED;bucket=2-7d@2026-07-15`, or
`liq:entity=LE-BANK-01;asset=CB-1@2026-07-15` for a counterbalancing asset. Every fired finding
cites the specific bucket/asset/category rows and the scenario it arose under.

## Freshness / effective dates

- The scenario/limit **config is a versioned contract**; the output records `config_version` so an
  analysis is reproducible for the same position and scenarios.
- As-of date and reporting horizon are stated in the output; behavioral assumptions (runoff,
  rollover, inflow realization) are those in effect for that config version.
- Market data and collateral valuations should be same-day as the as-of; note any staleness.

## Least-privilege operations (deployment)

- `alm.positions(entity_id, as_of)` → bounded, paged cash-flow items by bucket.
- `collateral.inventory(entity_id, as_of)` → assets with class, market value, base haircut.
- `deposits.funding(entity_id, as_of)` → deposit categorization and wholesale funding maturities.
- `marketdata.haircuts(as_of)` → prices/haircuts for collateral classes.
- `config.get('liquidity', version)` → stress rates, CBC add-ons, and limits.

All read-only, deterministic, durable `analysis_id`, below the fixed timeout; page a large book by
portfolio/desk as resumable stages. No mutating operations are bound by this skill.
