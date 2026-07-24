# Source Map — model-roll-forward-auditor

## Source hierarchy (highest first)
| Rank | Source (MCP integration) | Used for | Access |
| ---- | ------------------------ | -------- | ------ |
| 1 | Model version store (prior + current) | Line-item ending/opening balances | Read-only |
| 2 | Reference data | Line-item label normalization | Read-only |

The two model versions are the evidence; the audit never edits either and records both versions.

## Citation format
`{system}:{ref}` — e.g. `model:model=MDL-12;item=total_debt;v=prior->current`. Every break cites
the line item and both versions.

## Freshness / effective dates
- Both versions are used as supplied; if the current opening was manually overwritten, the break
  is surfaced, not reconciled away.

## Least-privilege operations (deployment)
- `model.read_version(model_id, version)` → line-item balances — read-only, bounded.
Durable `audit_id`; deterministic; below the fixed timeout; no mutation. MNPI barriers enforced.
