# Source Map — capital-structure-maturity-mapper

## Source hierarchy (highest first)
| Rank | Source (MCP integration) | Used for | Access |
| ---- | ------------------------ | -------- | ------ |
| 1 | Debt schedule / capitalization table (system of record) | Instruments, principal, seniority, maturity | Read-only |
| 2 | Reference data | Instrument-type/seniority normalization | Read-only |

The debt schedule is the system of record; the map never edits it and records the as_of date.

## Citation format
`{system}:{ref}@{as_of}` — e.g. `debt:company=CO-88;instrument=SN-1@2026-07-18`. Every bucket
total cites its contributing instrument lines.

## Freshness / effective dates
- All metrics are **as of** the supplied `as_of`; weighted-average maturity is measured from it.
- If instrument data spans multiple as-of dates, flag it rather than mixing.

## Least-privilege operations (deployment)
- `debt.read_schedule(company_id, as_of)` → instruments — read-only, bounded.
Durable `map_id`; deterministic; below the fixed timeout; no mutation. MNPI barriers enforced.
