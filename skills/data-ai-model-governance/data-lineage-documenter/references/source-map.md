# Source Map — data-lineage-documenter

## Source hierarchy (highest first)

| Rank | Source (MCP integration) | Used for | Access |
| ---- | ------------------------ | -------- | ------ |
| 1 | **Data catalog** (controlled content) | Data-product identity, datasets, owners, classifications, catalog lineage, retention policies | Read-only |
| 2 | **Model registry** | Model/feature-pipeline provenance for transformation nodes that score or enrich data | Read-only |
| 3 | **Data management policy / standard** (policy library) | Required attributes, retention schedule, lineage & BCBS 239 expectations | Read-only |
| 4 | **Data contracts** | Producer-declared schema, quality rules, and SLAs for source/ingestion nodes | Read-only |
| 5 | **Agent / tool execution logs** | Actual source-to-output flow for agentic/automated pipelines (steps, tools, I/O) | Read-only |
| 6 | **Risk & issue systems** | Open data-quality issues affecting a node (for routing, not resolution) | Read-only |

Precedence: the **data catalog** and **data-management policy** are authoritative for owners,
classifications, and retention; the **model registry** is authoritative for model/feature
provenance. Where a documented node conflicts with the catalog (e.g. a different owner), cite
both and mark the node `needs-data` for the steward to resolve — never silently pick one.

## Citation format

`{system}:{ref}@{version}` — e.g. `data-catalog:tbl/cb_loans@v5`, `source:REG-MDL-01`,
`transform:job:enrich_pdlgd@v3`, `source:POL-DM-01`. Every traced node and edge carries the
`source_id` it traces to. Record `spec_version` (the lineage methodology / catalog version) on
every document.

## Freshness / effective dates

- Read the **current** catalog record, owners, and classifications fresh; lineage documented
  against a superseded schema, owner, or retention policy is invalid.
- Provenance is a **versioned contract**: record each `source_id` and `spec_version` so the
  lineage basis is reproducible and reviewable.
- `as_of_date` frames flow/profile evidence drawn from agent/tool logs.

## Least-privilege operations (deployment)

- `catalog.get(product_id | dataset_ref)` → identity, owner, classification, retention, catalog
  lineage — read-only.
- `registry.get(model_id, version)` → model/feature provenance for scoring transformations —
  read-only.
- `policy.get(source_id)` / `contract.get(source_id)` → required attributes and quality rules —
  read-only.
- `logs.trace(pipeline, window)` → observed source-to-output steps for agentic pipelines —
  read-only.

No mutation from this skill. It **never** writes lineage back to the data catalog, updates a
registry record, resolves a data-quality issue, or records a governance decision. The drafted
lineage document is a proposal emitted for the data-governance owner / data steward via the
approval broker.
