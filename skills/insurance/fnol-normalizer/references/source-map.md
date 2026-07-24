# Source Map — fnol-normalizer

## Source hierarchy (highest first)
| Rank | Source (MCP integration) | Used for | Access |
| ---- | ------------------------ | -------- | ------ |
| 1 | Claims-intake record (system of record) | Raw FNOL fields | Read-only |
| 2 | Controlled-vocabulary config (versioned) | loss_type_map, cause_map, required_fields | Read-only |
| 3 | Reference data | State/geography normalization | Read-only |

The intake record is the system of record; the normalizer never edits the source and only emits
a proposed normalized view.

## Citation format
`{system}:{ref}` — e.g. `intake:fnol=FNOL-8801;field=loss_type_raw`. Every mapping and exception
cites the specific raw field.

## Freshness / effective dates
- Vocabulary config is a **versioned contract**; the output records the version used.

## Least-privilege operations (deployment)
- `intake.read_fnol(fnol_id)` → raw record — read-only, bounded.
- `config.get('fnol_vocab', version)` → maps + required fields — read-only.
Durable `normalization_id`; below the fixed timeout; no mutation.
