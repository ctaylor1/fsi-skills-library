# Source Map — payment-integration-readiness-pack

## Source hierarchy (highest first)
| Rank | Source (MCP integration) | Used for | Access |
| ---- | ------------------------ | -------- | ------ |
| 1 | Integration attestation/config record (system of record) | Item attestations, evidence refs | Read-only |
| 2 | Approved readiness-checklist config (versioned) | Required items, categories, gate items | Read-only |
| 3 | Reference data | Category normalization | Read-only |

The attestation record is the system of record; the pack never marks an item attested or changes
config.

## Citation format
`{system}:{ref}@{version}` — e.g. `attest:integration=INT-77;item=idempotency@2026-07-18`,
`checklist:go_live@v2026.05`. Every gap cites its item and the checklist version.

## Freshness / effective dates
- Checklist config is a **versioned contract**; the output records the version used.

## Least-privilege operations (deployment)
- `attest.read(integration_id)` → item attestations — read-only, bounded.
- `config.get('go_live_checklist', version)` → required items + gate flags — read-only.
Durable `packet_id`; below the fixed timeout; no mutation.
