# Source Map — buyer-investor-list-builder

## Source hierarchy (highest first)

| Rank | Source (MCP integration) | Used for | Access |
| ---- | ------------------------ | -------- | ------ |
| 1 | **Deal data room / VDR** + **deal-team CIM** | Target facts that anchor strategic-fit rationale | Read-only |
| 2 | **Filings / regulatory retrieval** | Buyer size, segments, prior M&A, capacity to transact | Read-only |
| 3 | **Market / financial data** | Market cap, dry powder, sector activity, deal-size fit | Read-only |
| 4 | **Research corpus** | Sector theses, sponsor mandates, precedent transactions | Read-only |
| 5 | **CRM** | Relationship strength, coverage history, prior outreach | Read-only |
| 6 | **Firm restricted / conflicts list** (versioned) | Restricted-list and conflict screen (screen only, never adjudicate) | Read-only |

Every fit-rationale claim and relationship note **must cite a document in the source index**
(rank 1–5). The restricted/conflicts list (rank 6) is a **versioned contract** used only to
flag candidates for hold; it does not clear or approve anyone.

## Citation format

`{source_doc}:p{page}@{version}` — e.g. `SRC-1:p12@v1`, `SRC-3:p2@v1`. Relationship context
cites CRM, e.g. `SRC-4:p8@v1`. The restricted screen records the list version, e.g.
`restricted-list@v2026.07`.

## Freshness / effective dates

- Market data and sponsor-mandate research must be within `freshness_window_days` (default
  120); stale sources are flagged and require a refresh before a candidate is placed.
- The restricted/conflicts list must be read **fresh** at build time — a candidate cleared on
  a stale list is not cleared.
- Every candidate record carries the as-of date and the source versions used, so the list is
  reproducible and reviewable.

## Conflict handling

- Conflicting sizing/mandate signals across sources are **surfaced**, not silently resolved:
  cite both and note the conflict in the rationale.
- A candidate whose only rationale cites a document **not** in the source index is an
  unsupported claim and is excluded (`needs-source`) — never "cited to the data room".

## Least-privilege operations (deployment)

- `dataroom.read(doc_id)`, `filings.read(entity_id)`, `marketdata.read(entity_id)`,
  `research.read(query)`, `crm.read(entity_id)` — all read-only, bounded payloads.
- `restricted.check(entity_id, version)` → boolean + list version (screen only; no clear).
- No mutation from this skill. Marking the list ready for external delivery is a **proposed**
  state recorded via the approval broker; the actual send is a human action.
