# Source Map — actuarial-model-run-assistant

## Source hierarchy (highest first)
| Rank | Source (MCP integration) | Used for | Access |
| ---- | ------------------------ | -------- | ------ |
| 1 | Reserving-data store (loss triangle, system of record) | Cumulative paid/incurred by origin × age | Read-only |
| 2 | Versioned **assumption config** | Method, tail factor, selection rules | Read-only |
| 3 | Reference data | Line/segment normalization | Read-only |

The triangle is the system of record; the run records the exact cells and assumptions used and
never edits the source.

## Citation format
`{system}:{ref}@{version}` — e.g. `reserving:triangle=WC-PAID-2026Q2@2026-06-30`,
`assumptions:chain_ladder@v2026.05`. The run packet records the triangle id and assumption version.

## Freshness / effective dates
- Assumption config is a **versioned contract**; the run records the version used.
- The evaluation date (latest diagonal) is taken from the triangle as supplied.

## Least-privilege operations (deployment)
- `reserving.read_triangle(triangle_id)` → cells + evaluation dates — read-only, bounded.
- `config.get('chain_ladder', version)` → method + tail factor — read-only.
Durable `run_id`; deterministic; below the fixed timeout; no mutation.
