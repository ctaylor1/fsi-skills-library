# Source Map — claim-damage-evaluation-comparator

## Source hierarchy (highest first)
| Rank | Source (MCP integration) | Used for | Access |
| ---- | ------------------------ | -------- | ------ |
| 1 | Claims document store (system of record) | Documents, line items, amounts, support links | Read-only |
| 2 | Reference data | Category/description normalization | Read-only |

The claims document store is the system of record; the comparison never edits a document or a
line item.

## Citation format
`{system}:{ref}` — e.g. `claims:claim=CLM-5501;doc=EST-A;item=IT-1`. Every finding cites the
specific line items and documents involved.

## Freshness / effective dates
- Use the documents as supplied; if a newer estimate supersedes an older one, cite both and flag
  the supersession as a data gap for the adjuster — never silently drop one.

## Least-privilege operations (deployment)
- `claims.read_documents(claim_id)` → documents + line items — read-only, bounded.
Durable `comparison_id`; below the fixed timeout; no mutation.
