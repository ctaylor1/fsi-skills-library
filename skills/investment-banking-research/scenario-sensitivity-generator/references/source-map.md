# Source Map — scenario-sensitivity-generator

## Source hierarchy (highest first)

| Rank | Source (MCP integration) | Used for | Access |
| ---- | ------------------------ | -------- | ------ |
| 1 | **Upstream base-case model** (dcf/comps/lbo/merger/3-statement) | Base driver values + output formulas (position of record) | Read-only |
| 2 | **Market / financial data** | Substantiate a driver only where the model cites it | Read-only |
| 3 | **Filings / research corpus** | Corroborate driver provenance | Read-only |
| 4 | Approved **assumption / config set** (versioned) | Scenario overrides, ranges, targets | Read-only |

The upstream model is authoritative for base drivers; this skill never re-originates a
valuation. If a driver source and the model conflict, cite both and flag — never silently
resolve.

## Citation format

Each driver carries a `source_ref` (e.g. `dcf:model=Acme-2026Q2;driver=ebitda_margin@2026-06-30`)
and a `provenance` string naming the upstream model/source. The pack records the
`config_version` and `as_of` so any run is reproducible.

## Freshness / effective dates

- `config_version` is a **versioned contract**; pin it so identical inputs reproduce
  identical numbers.
- Flag stale driver sources; do not refresh a driver silently.

## Least-privilege operations (deployment)

- `model.read(model_id)` → base drivers + formulas — read-only.
- `refdata.read(driver_ref, as_of)` → corroborating value + source — read-only.
- `config.get(config_version)` → scenario/range/target set — read-only.
All read-only, deterministic, durable `analysis_id`, below the fixed timeout; split large
two-way grids into resumable stages.
