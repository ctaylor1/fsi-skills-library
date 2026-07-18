# Source Map — procurement-sourcing-assistant

## Source hierarchy (highest first)

| Rank | Source (MCP integration) | Used for | Access |
| ---- | ------------------------ | -------- | ------ |
| 1 | **Procurement / sourcing (S2P)** | System of record for the sourcing event, `sourcing_id`, bidder responses, recorded approvals | Read-only |
| 2 | **Document intelligence** | Requirement documents, RFP/RFI content, bidder response documents, page/field citations | Read-only |
| 3 | **CRM / supplier master** | Supplier identity, incumbency, relationship context for the market scan | Read-only |
| 4 | **Contracts / CLM** | Existing agreements, incumbent terms, renewal dates informing requirements and risk | Read-only |
| 5 | **Knowledge base** | Category playbook, evaluation-weight standard, `required_sections`, `required_approvals` (versioned) | Read-only |
| 6 | **Project tracking / email & calendar** | Sourcing timeline, stakeholder owners, review milestones (context only) | Read-only |

The sourcing system state (event, bidder responses, approvals) wins on conflict; document
intelligence provides the evidencing artifacts. The category playbook (knowledge base) is the
authority on required sections, evaluation weights, and required approvals. This skill reads
only — it never writes back a pack, award, RFP issuance, or approval.

## Citation format

`{system}:{ref}@{date/version}` — e.g. `proc:event=SRC-4001@2026-07-16`,
`docintel:doc=REQ-1@2026-07-10`, `proc:bid=B-1-response@2026-07-15`,
`crm:supplier=S-1@2026-07-12`, `kb:category-playbook@2026.07`. Every asserted item
(requirement, supplier, bidder score, RFP section, risk input) carries a citation; an item
with no citable source is an open item or `needs-data`, never an assumed inclusion.

## Freshness / effective dates

- Bidder responses and approvals must be read fresh from the sourcing system (avoid working a
  superseded response version).
- `required_sections`, `evaluation_criteria` weights, `required_approvals`, and the pack
  template are **versioned contracts**; the versions are recorded on the manifest
  (`config_version`, `template_version`) for reproducibility and review.

## Least-privilege operations (deployment)

- `proc.read(sourcing_id)` → event, bidder responses, approvals — read-only.
- `docintel.get(doc_id)` / `docintel.cite(doc_id, field)` → documents + citations — read-only.
- `crm.read(supplier_id)` → supplier identity/incumbency — read-only.
- `clm.read(supplier_id)` → existing agreement context — read-only.
- `kb.get('category-playbook', version)` → required sections, weights, required approvals — read-only.
No mutation from this skill. The assembled pack is a **draft**; any award, RFP issuance,
delivery, or system-of-record change is a separate, human-approved step via the approval broker.
