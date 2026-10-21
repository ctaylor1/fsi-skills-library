# Source Map — merger-model-builder

## Source hierarchy (highest first)

| Rank | Source (MCP integration) | Used for | Access |
| ---- | ------------------------ | -------- | ------ |
| 1 | **Filed financials** (10-K/10-Q, position of record) | Acquirer/target net income, diluted shares | Read-only |
| 2 | **Market data** | Current share prices, share counts | Read-only |
| 3 | Deal-team **offer terms & financing plan** (versioned) | Offer price/premium, cash/stock mix, debt/cash sources, fees | Read-only |
| 4 | Deal-team **synergy & purchase-accounting estimates** | Run-rate synergies, phasing, intangible write-ups, amortization | Read-only |
| 5 | **Assumptions pack** (versioned) | Pro forma tax rate, default scenario drivers | Read-only |
| 6 | **Research corpus / data room** | Corroborating context, prior guidance | Read-only |

Standalone financial figures come from filings/market data, not from the deal team. Deal
drivers (premium, mix, financing, synergies, write-ups) come from the deal team's approved,
versioned terms. Never substitute a desired verdict for a sourced driver.

## Citation format

`{system}:{ref}@{date_or_version}` — e.g. `filings:ACQ;10-K;FY2025;net_income+diluted_shares`
or `dealteam:PROJECT-ATLAS;offer-terms-v3@2026-07-14`. Every driver in the model's
`assumptions` list carries its `source_ref`. Management estimates (synergies, write-ups) are
labelled as estimates, not facts.

## Freshness / effective dates

- The **assumptions pack** (tax rate, default scenario drivers) is a versioned contract; the
  output stamps `assumptions_version` into `model_id` so a run is reproducible.
- Share prices and share counts are as-of the model date; state the as-of.
- Offer terms and the financing plan are versioned; cite the exact version used.

## Least-privilege operations (deployment)

- `filings.get(entity, statement, period)` → net income, diluted shares.
- `marketdata.quote(entity)` → share price, shares outstanding.
- `dealroom.terms(deal_id, version)` → offer/premium, consideration mix, financing plan.
- `dealroom.estimates(deal_id, version)` → synergies, purchase-accounting write-ups.
- `assumptions.get('merger', version)` → tax rate + default scenario drivers.
- `calc.pro_forma(...)` → deterministic computation via the bundled engine.

All read-only, deterministic, durable `model_id`, below the fixed timeout; scenarios and the
sensitivity grid are computed as resumable stages.
