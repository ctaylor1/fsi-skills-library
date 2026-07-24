# Source Map — liability-evidence-matrix-builder

## Source hierarchy (highest first)
| Rank | Source (MCP integration) | Used for | Access |
| ---- | ------------------------ | -------- | ------ |
| 1 | Claim file (system of record) | Alleged facts, evidence items, references | Read-only |
| 2 | Document/evidence store | Underlying evidence documents | Read-only |
| 3 | Reference data | Party/evidence-type normalization | Read-only |

The claim file is the system of record; the matrix never edits it and only maps existing facts
and evidence.

## Citation format
`{system}:{ref}` — e.g. `claim:claim=CLM-6602;evidence=EV-3`. Every matrix cell cites the specific
evidence items.

## Freshness / effective dates
- Use facts/evidence as recorded; if evidence is superseded, cite both and flag rather than
  dropping.

## Least-privilege operations (deployment)
- `claim.read_facts(claim_id)` → facts — read-only, bounded.
- `claim.read_evidence(claim_id)` → evidence + references — read-only.
Durable `matrix_id`; below the fixed timeout; no mutation.
