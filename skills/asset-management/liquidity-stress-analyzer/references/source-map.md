# Source Map — liquidity-stress-analyzer

## Source hierarchy (highest first)

| Rank | Source (MCP integration) | Used for | Access |
| ---- | ------------------------ | -------- | ------ |
| 1 | **PMS/OMS** holdings (position of record) | Positions, market value, NAV, base currency | Read-only |
| 2 | **Market data** | ADV, bid/ask spread, price, and stress reference levels | Read-only |
| 3 | **Risk / performance** systems | Derivative notionals, margin/collateral, buffer balances | Read-only |
| 4 | Liquidity-risk **config** (versioned) | Metric thresholds and band mapping | Read-only |
| 5 | **Scenario** definition (versioned) | Stress assumptions (ADV haircut, spread multiple, price shock, redemption) | Read-only |
| 6 | **Research / compliance rules** | Context and applicable liquidity-rule references (not a breach finding) | Read-only |

Never substitute a modeled or assumed liquidity figure for the market-data record. If two
sources conflict (e.g., PMS market value vs. a risk-system valuation), cite both and flag for
the reviewer.

## Citation format

`pos:{source_ref}@{as_of}` — e.g. `pos:pms=AM-BALANCED-01;pos=P-4@2026-07-15`. Every breached
metric cites the specific position rows and records the basis (threshold, scenario) used.

## Freshness / effective dates

- Config (thresholds, band mapping) is a **versioned contract**; the output records the
  `config_version` so an analysis is reproducible.
- Scenario assumptions are recorded verbatim in `scenario_assumptions`; a stress result is
  meaningless without them.
- ADV, spread, and price are point-in-time; state the `as_of` and treat them as estimates,
  especially under stress (apply the scenario `adv_haircut`).

## Least-privilege operations (deployment)

- `pms.holdings(portfolio_id, as_of)` → positions, market value, NAV, base currency.
- `marketdata.liquidity(instrument)` → ADV, spread, price.
- `risk.margin(portfolio_id, as_of)` → derivative notionals, posted collateral, buffer.
- `config.get('liquidity', version)` → thresholds + band mapping.
- `scenario.get(name, version)` → stress assumptions.

All read-only, deterministic, durable `analysis_id`, below the fixed timeout; page long books
as resumable stages.
