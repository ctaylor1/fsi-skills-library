# Source Map — transaction-cost-estimator

## Source hierarchy (highest first)
| Rank | Source (MCP integration) | Used for | Access |
| ---- | ------------------------ | -------- | ------ |
| 1 | OMS/EMS **execution record** (system of record) | Side, qty, arrival/exec price & time, fills | Read-only |
| 2 | **Market/reference data** | Arrival/VWAP/close, ADV, volatility | Read-only |
| 3 | Approved **TCA-methodology config** (versioned) | Impact model + coefficients, spread/commission assumptions | Read-only |

Never substitute a user-typed benchmark for the market-data record; cite every input.

## Citation format
`{system}:{ref}@{ts/version}` — e.g. `oms:order=ORD-7001@2026-07-18T14:00`,
`mktdata:AAPL;adv,vol@2026-07-18`, `tca:methodology@v2026.04`. Every component cites its inputs.

## Freshness / effective dates
- Methodology config is a **versioned contract**; the output records the version.
- Benchmarks are as-of the trade date/interval; flag mixed or stale as-of.

## Least-privilege operations (deployment)
- `oms.read_execution(order_id)` → order + fills — read-only.
- `mktdata.read(security, date)` → arrival/vwap/close/adv/vol — read-only.
- `config.get('tca', version)` → methodology — read-only.
Durable `tca_id`; below the fixed timeout; deterministic; no market action.
