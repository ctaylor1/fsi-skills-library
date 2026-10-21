# Source Map — model-roll-forward-auditor

Each balance must be explicitly numeric or null (structural break), with explicit nonnegative numeric tolerance. Model prior/current version strings and unique line_item IDs are required.


## Version 0.2.0 contract

The native result is a closed calculation record. Retain the original input separately and validate with `python3 scripts/validate_output.py RESULT.json --input ORIGINAL.json`; `--selftest` loads both bundled examples. Computation validates input first. Finite JSON numbers, valid dates, supported domains and unique identifiers are enforced; duplicate JSON keys are rejected. Output validation reconstructs from the original and rejects omitted, altered or extra results, including flags/counts/statuses. Keep author narrative and workflow envelopes outside the native result. Source binding establishes deterministic fidelity to supplied inputs, not source authenticity, data rights, economic validity, institutional acceptance or independent assurance.


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
