# Source Map — client-rfq-preparation-brief

## Source hierarchy (highest first)
| Rank | Source (MCP integration) | Used for | Access |
| ---- | ------------------------ | -------- | ------ |
| 1 | CRM / client system of record | Tier, KYC/AML status, jurisdiction, restricted products | Read-only |
| 2 | Instrument reference | Instrument type/details normalization | Read-only |
| 3 | Prior-activity feed | Recent trades/inquiries with the client | Read-only |
| 4 | Suitability policy config (versioned) | Flag rules (KYC, restricted product, jurisdiction) | Read-only |

CRM is the client system of record; the brief never edits it and only assembles a read-only view.

## Citation format
`{system}:{ref}` — e.g. `crm:client=****8841;field=kyc_status`, `ref:instrument=OPT-XYZ`. Every
flag and section cites its source.

## Freshness / effective dates
- KYC/suitability status is used as of the CRM read; a stale status is surfaced as a flag.
- Suitability policy is a **versioned contract**; the output records the version used.

## Least-privilege operations (deployment)
- `crm.read_client(client_id)` → context — read-only, bounded.
- `activity.read(client_id)` → prior activity — read-only.
- `config.get('suitability_policy', version)` → flag rules — read-only.
Durable `brief_id`; below the fixed timeout; no mutation; no pricing.
