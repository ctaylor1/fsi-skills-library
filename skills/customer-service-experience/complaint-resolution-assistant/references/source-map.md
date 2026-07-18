# Source Map — complaint-resolution-assistant

## Source hierarchy (highest first)

| Rank | Source (MCP integration) | Used for | Access |
| ---- | ------------------------ | -------- | ------ |
| 1 | **Complaint / case management** | Complaint record + state (system of record), `complaint_id` | Read-only |
| 2 | **CRM** | Customer profile, product holdings, vulnerability flags, prior contacts | Read-only |
| 3 | **Contact-center transcripts** | Interaction evidence for the chronology (calls, chats, emails) | Read-only |
| 4 | **Approved knowledge / product terms** | Applicable standards, disclosures, and product terms | Read-only |
| 5 | **Approved-calculation service** | Redress arithmetic (interest, D&I band, goodwill cap) | Read-only |
| 6 | Versioned **redress config**, **standards map**, **root-cause map** | Classification + remediation | Read-only |

## Citation format

`{system}:{ref}@{date/version}` — e.g. `casemgmt:cmp=CMP-3001@2026-07-15`,
`crm:cust=C-100@2026-07-01`, `terms:credit_card-fees@v2026.05`,
`config:crx-redress@crx-2026.07`.

## Freshness / effective dates

- Complaint state must be read fresh (avoid drafting on an already-resolved complaint).
- Standards and product terms are effective-dated: assess the complaint against the terms in
  force **at the time of the events**, not today's terms.
- Redress config, standards map, and root-cause map are **versioned**; the version is
  recorded on every draft package for reproducibility and review.

## Least-privilege operations (deployment)

- `complaints.read(complaint_id)`, `complaints.find(customer_id, product)` — read-only.
- `crm.summary(customer_id)`, `transcripts.read(interaction_id)` — read-only, bounded.
- `terms.get(product, effective_date)`, `knowledge.get(topic)` — read-only.
- `config.get('crx-redress'|'crx-standards'|'crx-rootcause', version)` — read-only.
No mutation from this skill. Sending the response, paying redress, changing an account, or
filing a regulatory return is performed elsewhere (human owner or
`omnichannel-case-orchestrator`) **only** via the approval broker, and is out of scope here.
