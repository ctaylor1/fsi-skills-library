# Domain Rules — data-lineage-documenter

Orientation references: BCBS 239 (risk data aggregation & reporting — completeness, accuracy,
timeliness, and end-to-end lineage), the firm's Data Management Standard and Data Governance
Policy, DAMA-DMBOK (data lineage & metadata management), and, for model-feature pipelines, SR
11-7 (model data traceability). The firm's **data-lineage methodology** and its **data catalog**
take precedence and are versioned contracts (`spec_version`). The document produced here is a
DRAFT for a data-governance owner and data steward to review and approve; it is never a
certification or an accuracy/regulatory-fitness determination.

## Node layers (the approved taxonomy — the ONLY layers permitted)

| Layer | What it captures | Typical systems |
| ----- | ---------------- | --------------- |
| `source` | System-of-record origin of the data | Core banking, market data, CRM |
| `ingestion` | Extract/load into the platform | Ingestion/ETL platform, landing zone |
| `transformation` | Cleansing, joins, enrichment, model scoring | Feature engine, ETL/ELT jobs |
| `store` | Persisted governed store | Data warehouse, data mart, lake |
| `feature` | Derived features / marts consumed downstream | Feature store, semantic layer |
| `output` | Report, extract, API, or dataset delivered to a consumer | Reg-reporting platform, BI, API |

A node whose `layer` is outside this taxonomy is `needs-data` (map it first — never invent a
layer). A lineage graph must have at least one `source` and at least one `output` node.

## Required documented attributes by data-product criticality (deterministic)

| Criticality | Required node attributes |
| ----------- | ------------------------ |
| **High** | owner, provenance, classification, controls, quality_rules, retention |
| **Medium** | owner, provenance, classification, controls, retention |
| **Low** | owner, provenance |

`owner` and `provenance` are **structural** — a node missing either is `needs-data` (you cannot
document lineage without a steward and a traced origin). The remaining attributes are
**documentation** requirements — a node missing one for its criticality is `control-gap`.
These are configuration, not judgment, and are overridable only through the versioned
methodology.

## Provenance (never invent a source)

- A node/edge whose `source_id` is in `authoritative_sources` is `traced`.
- A node/edge with no `source_id`, or one not in `authoritative_sources`, is `untraced` — a
  node is `needs-data`; an edge is `undocumented-transform`. An untraced lineage element is
  **never** presented as `ready-for-review`.
- Authoritative sources are the data catalog, model registry, agent/tool logs, data contracts,
  and the data-management policy — not an analyst's assertion or an ad-hoc spreadsheet.

## Graph integrity (deterministic)

- **Dangling edge** — an edge whose `from_node`/`to_node` is not a documented node.
- **Orphan node** — a non-`source` node with no inbound edge (its upstream lineage is undocumented).
- **Cycle** — lineage must be a DAG; a cycle means the dependency documentation is inconsistent.
- The graph is **sound** only when it has a `source`, has an `output`, is cycle-free, has no
  orphan nodes, and has no dangling edges.

## Node / edge statuses (this skill may set only these)

- Per node: `ready-for-review` | `control-gap` | `orphan-node` | `needs-data`.
- Per edge: `ready-for-review` | `undocumented-transform` | `dangling-edge`.
- Package: `draft-incomplete` | `ready-for-governance-review`. A package is
  `ready-for-governance-review` only when every node and edge is `ready-for-review`, the graph
  is sound, and coverage is complete. It may **not** be set to `certified`, `attested`,
  `approved`, or any accuracy/fitness result.

## Hard boundaries (fail closed)

- No **certification / attestation** of the lineage; no data-accuracy, completeness, or
  regulatory-fitness (e.g. BCBS 239) determination.
- No **self-approval**; `governance_approval` stays `pending` and needs a human data-governance
  owner + data-steward sign-off.
- No **invented source**; an untraced node/edge is `needs-data` / `undocumented-transform`,
  never forced to `ready-for-review`.
- No **write** to the data catalog, model registry, or any system of record — the document is a
  draft proposal only.

## Lineage document — required contents

`spec_version`; data-product identity + criticality; per-node record (layer, system, owner,
classification, provenance with the traced source, controls, quality rules, retention, status,
gaps, citations); per-edge record (from/to, transformation, provenance, status, citations);
graph-integrity summary; criticality-scaled coverage matrix; approvals block
(`governance_approval: pending`, `reviewer_signoff_required: true`); summary counts; the
standing note.
