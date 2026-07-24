# Source Map — actuarial-data-lineage-checker

## Source hierarchy (highest first)
| Rank | Source (MCP integration) | Used for | Access |
| ---- | ------------------------ | -------- | ------ |
| 1 | Policy-admin / claims / actuarial **data store** (system of record) | Exposure, premium, loss, claim, policy records | Read-only |
| 2 | **Data-definition registry** (versioned) | Field definitions and their versions | Read-only |
| 3 | Reconciliation **config** (versioned) | Movement thresholds, expected periods | Read-only |

Never alter the source dataset; cite every break to its record(s) and definition version.

## Citation format
`{system}:{ref}@{period/version}` — e.g. `actl:dataset=loss;key=LOB-AUTO;period=2025Q4@def-v3`,
`config:lineage@v2026.03`. Every break cites the record(s) and definition version involved.

## Freshness / effective dates
- Definition registry and thresholds are **versioned contracts**; the output records versions.
- Reconcile named periods; flag mixed as-of.

## Least-privilege operations (deployment)
- `actl.read(dataset, period)` → records — read-only, bounded.
- `defreg.get(metric)` → definition version — read-only.
- `config.get('lineage', version)` → thresholds/expected periods — read-only.
Durable `lineage_id`; deterministic; no mutation of source data.
