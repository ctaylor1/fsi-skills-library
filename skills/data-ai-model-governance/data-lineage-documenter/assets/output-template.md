# Data Lineage Document — DRAFT (for data-governance review)

> Draft data-lineage documentation for human review only; this skill does not certify, attest
> to, or approve the lineage, makes no data-accuracy or regulatory-fitness determination, and
> writes nothing to the data catalog or any system of record — a data-governance owner and data
> steward must review and approve before use.

Fill every `{{placeholder}}` from an authoritative source (data catalog, model registry,
data-management policy, data contract, agent/tool log). Do not assert an owner, control,
retention, or transformation that is not traced to a source; mark any untraced element
`needs-data` (node) or `undocumented-transform` (edge). Do not add certification, attestation,
accuracy/fitness, or catalog-write language.

## 1. Data product

| Field | Value |
| ----- | ----- |
| Product id | {{product_id}} |
| Name | {{name}} |
| Domain | {{domain}} |
| Criticality | {{criticality}} |
| Catalog reference | {{catalog_ref}} |
| Lineage methodology version | {{spec_version}} |
| As of | {{as_of_date}} |

## 2. Source-to-output nodes

One row per lineage stage. `Provenance` shows the value **and** the source it traces to (a
`source_id`), or `untraced`. No node is `ready-for-review` without an owner, a traced
provenance, and the attributes its criticality requires.

| Node id | Layer | Name / system | Owner (steward) | Classification | Provenance | Controls | Quality rules | Retention | Status |
| ------- | ----- | ------------- | --------------- | -------------- | ---------- | -------- | ------------- | --------- | ------ |
| {{node_id}} | {{layer}} | {{name}} / {{system}} | {{owner}} | {{classification}} | {{provenance_status}} ({{source_id}}) | {{controls}} | {{quality_rules}} | {{retention_policy_id}} / {{retention_period}} | {{status}} |

Node status legend: `ready-for-review` (owner + traced provenance + required attributes +
connected) · `control-gap` (a required control / quality rule / retention / classification is
missing for the criticality) · `orphan-node` (non-source node with no inbound dependency) ·
`needs-data` (unknown layer, missing owner, or untraced provenance).

## 3. Dependencies and transformations

One row per edge. Each edge documents the transformation from one node to the next and the
source it traces to.

| Edge id | From | To | Transformation | Provenance | Status |
| ------- | ---- | -- | -------------- | ---------- | ------ |
| {{edge_id}} | {{from_node}} | {{to_node}} | {{transformation}} | {{provenance_status}} ({{source_id}}) | {{status}} |

Edge status legend: `ready-for-review` (documented transformation traced to a source between two
known nodes) · `undocumented-transform` (no transformation, or untraced) · `dangling-edge`
(references a node that is not documented).

## 4. Graph integrity and coverage

| Check | Value |
| ----- | ----- |
| Has source node | {{has_source}} |
| Has output node | {{has_output}} |
| Cycle-free (DAG) | {{cycle_free}} |
| Orphan nodes | {{orphan_nodes}} |
| Dangling edges | {{dangling_edges}} |
| Graph sound | {{graph_sound}} |
| Required node attributes ({{criticality}}) | {{required_node_attributes}} |
| Nodes ready / total | {{nodes_ready}} / {{nodes_total}} |
| Edges ready / total | {{edges_ready}} / {{edges_total}} |
| Coverage complete | {{coverage_complete}} |

## 5. Open items before the lineage can be approved

- [ ] Every `needs-data` node given an owner/steward, a valid layer, and a traced source.
- [ ] Every `control-gap` node given the missing control / quality rule / retention / classification.
- [ ] Every `orphan-node` given its documented inbound dependency (or removed if out of scope).
- [ ] Every `undocumented-transform` edge given a documented, source-traced transformation.
- [ ] Every `dangling-edge` repointed to a documented node (or removed).
- [ ] Source and output nodes present; graph confirmed cycle-free (sound).

## 6. Approvals (required before any use)

| Field | Value |
| ----- | ----- |
| Governance approval | {{governance_approval}} (must be `pending` from this skill) |
| Reviewer sign-off required | {{reviewer_signoff_required}} |
| Steward attestation required | {{steward_attestation_required}} |
| Approver role | {{approver_role}} |

- [ ] Node owners, classifications, controls, and retention reviewed against the catalog/policy.
- [ ] Every provenance confirmed traced to an authoritative source.
- [ ] Graph confirmed sound (source, output, cycle-free, no orphans, no dangling edges).
- [ ] Lineage approved for use / catalog recording by the named authorized owner (not this skill).

Reviewer: ________________________  Steward: ________________________  Date: ____________
Decision: approve / revise / reject

## 7. Standing note

Draft data-lineage documentation for human review only; this skill does not certify, attest to,
or approve the lineage, makes no data-accuracy or regulatory-fitness determination, and writes
nothing to the data catalog or any system of record — a data-governance owner and data steward
must review and approve before use.
