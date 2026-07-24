# Source Map — market-window-readiness-pack

## Source hierarchy (highest first)
| Rank | Source (MCP integration) | Used for | Access |
| ---- | ------------------------ | -------- | ------ |
| 1 | Deal attestation/config record (system of record) | Item attestations, evidence refs | Read-only |
| 2 | Approved launch-checklist config (versioned) | Required items, categories, gate items | Read-only |
| 3 | Reference data | Category normalization | Read-only |

The attestation record is the system of record; the pack never marks an item attested or changes
config.

## Citation format
`{system}:{ref}@{version}` — e.g. `attest:deal=DEAL-31;item=due_diligence@2026-07-18`,
`checklist:launch@v2026.05`. Every gap cites its item and the checklist version.

## Freshness / effective dates
- Checklist config is a **versioned contract**; the output records the version used.

## Least-privilege operations (deployment)
- `attest.read(deal_id)` → item attestations — read-only, bounded.
- `config.get('launch_checklist', version)` → required items + gate flags — read-only.
Durable `packet_id`; below the fixed timeout; no mutation. MNPI barriers enforced.
