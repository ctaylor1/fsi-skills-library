# Source Map — financing-alternatives-calculator

## Source hierarchy (highest first)
| Rank | Source (MCP integration) | Used for | Access |
| ---- | ------------------------ | -------- | ------ |
| 1 | Documented deal inputs / term sheets | Amount, rates, fees, term, equity terms | Read-only |
| 2 | Reference data | Share count, currency normalization | Read-only |

Terms are documented inputs; the calculator does not fetch live market rates and records each
term used.

## Citation format
`{system}:{ref}@{as_of}` — e.g. `terms:request=REQ-9;alt=TL@2026-07-18`. Each worksheet row
records the alternative id and the terms used.

## Freshness / effective dates
- All metrics are **as of** the supplied `as_of`; rates/fees are the documented inputs.

## Least-privilege operations (deployment)
- `terms.read(request_id)` → alternatives + terms — read-only, bounded.
Durable `calc_id`; deterministic; below the fixed timeout; no mutation. MNPI barriers enforced.
