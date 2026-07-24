# Source Map — claim-settlement-authority-packet

## Source hierarchy (highest first)
| Rank | Source (MCP integration) | Used for | Access |
| ---- | ------------------------ | -------- | ------ |
| 1 | Claim / evaluation record (system of record) | Claim summary, indemnity/expense estimates | Read-only |
| 2 | Authority-matrix config (versioned) | Tier caps + approver roles | Read-only |
| 3 | Document/evidence store | Supporting-evidence index | Read-only |
| 4 | Reference data | Role/tier normalization | Read-only |

The claim/evaluation record is the system of record; the packet never edits it and only looks up
the required tier from the matrix.

## Citation format
`{system}:{ref}@{version}` — e.g. `claim:claim=CLM-7003;evaluation@2026-07-18`,
`matrix:settlement_authority@v2026.05`. The tier and each item cite their source.

## Freshness / effective dates
- The authority matrix is a **versioned contract**; the output records the version used.
- Exposure figures are taken from the supplied evaluation; the packet does not re-estimate.

## Least-privilege operations (deployment)
- `claim.read_evaluation(claim_id)` → indemnity/expense — read-only, bounded.
- `config.get('settlement_authority', version)` → tiers — read-only.
Durable `packet_id`; below the fixed timeout; no mutation.
