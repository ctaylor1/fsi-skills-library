# Source Map — due-diligence-packager

## Source hierarchy (highest first)

| Rank | Source (MCP integration) | Used for | Access |
| ---- | ------------------------ | -------- | ------ |
| 1 | **Data room / VDR** (system of record for diligence docs) | Source index, every extraction/issue/open-question citation, versions | Read-only |
| 2 | **Document intelligence** | Page/clause/field extraction and citation from data-room docs | Read-only |
| 3 | **Filings** (regulatory / public) | Corroboration of public figures; never replaces a VDR citation | Read-only |
| 4 | **Market / financial data** | Corroboration and context (trading data, benchmarks) | Read-only |
| 5 | **Research corpus** | Background and thematic context | Read-only |
| 6 | **CRM** | Deal team, relationship, and contact context (masked) | Read-only |

The **data room is authoritative** for diligence content. A public/filing/market figure may
corroborate a VDR figure but cannot substitute for a data-room citation in the pack. When two
sources conflict, cite both and raise an issue — do not silently resolve.

## Citation format

`{doc_id}:p{page}@{version}` — e.g. `DOC-001:p12@final`, `DOC-003:p2@2026-Q1`. Each cited item
also carries the raw `source_doc` (doc id) so `validate_output` can resolve it against the
source index. Every extracted-data point and every issue must resolve to a doc in the index.

## Freshness / effective dates

- Each source doc carries a `date` and `version`; the pack records the deal `as_of_date`.
- Documents past the engagement freshness window are flagged for a refreshed source rather
  than used silently.
- The model-handoff bundles record the `pack_id` and generation date so downstream modeling
  consumes a versioned, reproducible input.

## Least-privilege operations (deployment)

- `vdr.index(deal_id)`, `vdr.read(doc_id)` — read-only document index and content.
- `docintel.extract(doc_id, field|page)` — read-only extraction with page citation.
- `filings.read(entity)`, `marketdata.read(ticker|series)` — read-only corroboration, bounded.
- `crm.read(deal_id)` — read-only deal/relationship context (masked).
No mutation from this skill. The drafted pack is written to a **controlled internal workspace
only**; external delivery is a separate, human-performed, approval-gated action and is never
executed here.
