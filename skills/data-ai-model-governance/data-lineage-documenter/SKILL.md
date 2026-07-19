---
name: data-lineage-documenter
description: >-
  Document end-to-end data lineage for a dataset, data product, or feature pipeline: map every
  source-to-output node with its transformations, owners, data classification, controls, quality
  rules, retention, and dependencies; trace each node and edge to an authoritative
  source (data catalog, model registry, agent/tool logs); check graph integrity (cycle-free, no
  orphan or dangling nodes); and assemble a lineage document as a DRAFT for data-governance
  review. Use when a data-governance lead, data engineer, or control owner needs
  to document or map lineage, capture dependencies and transformations, evidence
  controls/quality/retention per node, or prepare a lineage pack for BCBS 239, model-risk, or
  catalog review. Drafts ONLY: never certifies, attests
  to, or approves the lineage, never asserts the data is accurate or fit for regulatory reporting,
  never invents a source it cannot trace, never writes to the data catalog or any system of
  record, and never self-approves - a governance owner and steward approve first.
license: MIT
compatibility: Amazon Quick Desktop; requires data-catalog, model-registry, policy/data-management-standard, data-contract, agent/tool-log, and risk/issue MCP integrations (all read-only; the lineage document is drafted, never written back to the catalog).
metadata:
  aws-fsi-category: "Data, AI & Model Governance"
  aws-fsi-skill-type: "Artifact-creation skills"
  aws-fsi-risk-tier: "R3"
  aws-fsi-archetype: "Draft & package"
  aws-fsi-agent-pattern: "Interactive production copilot"
  aws-fsi-delivery-wave: "Wave 3 - regulated casework"
  aws-fsi-action-mode: "Draft-only; no system-of-record change"
  aws-fsi-scheduled-agent: "no"
  aws-fsi-baseline-status: "new"
  aws-fsi-human-approval: "required"
  aws-fsi-data-classification: "Confidential"
  aws-fsi-jurisdictions: "US (default); configure additional jurisdiction packs per deployment"
  aws-fsi-owner: "AI / Model Risk Governance"
  aws-fsi-primary-user: "Data governance / data engineering / control owner"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-07-17"
---

# Data Lineage Documenter

## Purpose and outcome
Turn a data product and its authoritative sources into an audit-ready, source-linked **data
lineage document (DRAFT)**: every source-to-output node with its layer, owner, classification,
controls, data-quality rules, and retention; every dependency edge with its transformation; each
node and edge traced to an authoritative source; a graph-integrity check (source and output
present, cycle-free, no orphan or dangling nodes); and a coverage matrix scaled to the product's
criticality. The outcome is a review-ready lineage document (or a clear, itemized list of what
blocks it) that a data-governance owner and data steward approve before it is relied on for
regulatory reporting, model documentation, or a catalog record. The skill never certifies,
attests to, or approves the lineage, and writes nothing back to the catalog.

## Use when
- "Document / map the lineage for data product DP-XXXX (or this model-feature pipeline)."
- "Capture the source-to-output dependencies and transformations for this dataset."
- "Evidence the controls, quality rules, and retention on each stage for BCBS 239 review."
- "Prepare the data-lineage / traceability pack for model-risk or catalog governance review."

## Do not use
- **Investigating a data-quality defect** (root cause, impact, remediation) → `data-quality-issue-investigator`.
- **Maintaining the inventory record** (ownership, materiality, lifecycle) → `model-inventory-maintainer`.
- **Classifying** the use case or setting inherent criticality → `ai-use-case-intake-classifier`.
- **Assembling the model-risk / validation documentation** pack → `model-risk-documenter`.
- **Assessing** data/privacy/third-party AI risk → `ai-risk-assessment-builder`.
- **Scoping a proposed change's** dependency impact / revalidation → `model-change-impact-analyzer`.
- Any request to **certify, attest, approve, or write the catalog** → refuse; draft only and route
  to a data-governance owner and steward.

## Adjacent-skill handoffs
See [references/handoffs.md](references/handoffs.md). This skill is lineage *documentation* only.
It consumes the product id + criticality from intake/inventory and provenance from the catalog/
registry, and emits a `spec_version`-keyed draft document with `governance_approval: pending`.
Issue investigation, model-risk documentation, risk assessment, change-impact analysis, and
catalog recording belong to the routes above or to an authorized human.

## Inputs and prerequisites
- The build request: `spec_version`, the `data_product` (`product_id`, `criticality` in
  High/Medium/Low, plus name/domain/catalog ref), the `authoritative_sources` list (data catalog,
  model registry, policy, data contract, agent/tool log — each with a `source_id`), the `nodes`
  (each: `node_id`, `layer`, and its owner/classification/`source_id`/controls/quality_rules/
  retention), and the `edges` (each: `edge_id`, `from_node`, `to_node`, `transformation`,
  `source_id`). Schema: [scripts/validate_input.py](scripts/validate_input.py).
- Read access to the data catalog, model registry, policy/data-management standard, data
  contracts, and agent/tool logs.

## Source hierarchy
See [references/source-map.md](references/source-map.md). The data catalog and data-management
policy are authoritative for owners, classifications, and retention; the model registry for
model/feature provenance; data contracts for quality rules. Cite every node and edge. Provenance
is a **versioned contract** — record `spec_version` and each `source_id` on every document.

## Workflow
1. **Validate & normalize** — run `validate_input`; confirm the data product, authoritative
   sources, nodes, and edges are structurally complete; warn on gaps that will force
   `needs-data` / `control-gap` / `orphan-node` / `undocumented-transform` / `dangling-edge`.
2. **Build deterministically** — run
   [scripts/calculate_or_transform.py](scripts/calculate_or_transform.py): resolve each node/edge
   provenance against the authoritative sources, check the required documented attributes for the
   criticality, detect orphans, dangling edges, and cycles, and assign a status. Rules:
   [references/domain-rules.md](references/domain-rules.md).
3. **Assign status** — per node: `needs-data`, `orphan-node`, `control-gap`, or
   `ready-for-review`; per edge: `dangling-edge`, `undocumented-transform`, or `ready-for-review`;
   package: `draft-incomplete` until the graph is sound and every element is ready, then
   `ready-for-governance-review`.
4. **Draft the document** — assemble from [assets/output-template.md](assets/output-template.md):
   product identity, node table, dependency/transformation table, graph-integrity and coverage,
   open items, and the approvals block. No owner, control, or transformation without a traced
   source or an explicit gap flag.
5. **Validate output** — run
   [scripts/validate_output.py](scripts/validate_output.py); fail closed on any miss.
6. **Never certify or write** — hand the reviewed draft to a data-governance owner and steward for
   approval; catalog recording is a separate, human, entitled action.

## Validation loop
Run `validate_input` before and `validate_output` after. The output screen enforces: template
fidelity + full per-node/edge fields; approved-source-only tracing for anything `ready`; no
invented/untraced provenance; graph & coverage integrity; `governance_approval == pending` and
`reviewer_signoff_required`; no certification/attestation/accuracy or catalog-write language;
standing note present. See [references/controls.md](references/controls.md). Correct and re-run
until it passes or the document is flagged `draft-incomplete`.

## Human approval
`required`. A data-governance owner (Data Governance Office / Chief Data Office) and the
accountable data steward must review and approve the lineage, its controls, and its retention
before it is relied on for regulatory reporting, model documentation, or a catalog record. This
skill drafts and packages; it never certifies, attests, writes the catalog, or self-approves.
Authoring the lineage and attesting to it are segregated duties.

## Failure handling
- **Unknown / out-of-taxonomy layer** → `needs-data`; map it to the 6-layer taxonomy first; do
  not invent a layer.
- **Missing owner/steward** → `needs-data`; never assign an owner to fill a gap.
- **Untraced node/edge** → `needs-data` / `undocumented-transform`; never promote an unsourced
  element to `ready-for-review`.
- **Non-source node with no inbound edge** → `orphan-node`; surface the undocumented upstream.
- **Edge to an unknown node** → `dangling-edge`; do not silently drop it.
- **Cycle detected** → mark the graph not sound; a lineage must be a DAG.
- **Tool timeout / stale sources** → return partial output with an explicit incomplete flag and
  the `spec_version` used; no retry assumption.

## Output contract
1. **Node table** — per node: `node_id`, `layer`, owner, classification, provenance with source,
   controls, quality rules, retention, and `status`; plus status counts.
2. **Dependency table** — per edge: `from`/`to`, transformation, provenance, and `status`.
3. **Graph integrity + coverage** — source/output present, cycle-free, orphans, dangling edges,
   soundness; required node attributes for the criticality and `complete`.
4. **Lineage document** (draft) — following [assets/output-template.md](assets/output-template.md),
   with the approvals block (`governance_approval: pending`, `reviewer_signoff_required: true`).
5. **Open items** — every `needs-data` / `control-gap` / `orphan-node` / `undocumented-transform`
   / `dangling-edge` element with what it needs.
6. **Machine-readable** — the lineage records keyed by `node_id` / `edge_id` with `spec_version`.
7. **Standing note** — "Draft data-lineage documentation for human review only; this skill does
   not certify, attest to, or approve the lineage, makes no data-accuracy or regulatory-fitness
   determination, and writes nothing to the data catalog or any system of record - a
   data-governance owner and data steward must review and approve before use."

## Privacy and records
**Confidential.** Lineage metadata can reveal sensitive data locations and flows; reference
datasets and systems by catalog id and node id rather than embedding records (data
minimization). Classification is documented per node, not assumed. Retain the drafted document,
`spec_version`, source citations, and reviewer/steward sign-off with the data-product record per
data-governance recordkeeping; log every read and every document produced with the author
identity.

## Gotchas
- **Documenting ≠ certifying.** The document is a draft map; a human owner and steward approve
  it and attest to its accuracy. Never emit "certified", "accurate", "fit for regulatory
  reporting", or catalog-write language.
- **Never invent a source.** A node/edge with no traceable authoritative source is `needs-data`
  / `undocumented-transform`, not a `ready-for-review` element with an assumed origin.
- **Coverage is criticality-scaled.** A High-criticality product needs owner, classification,
  controls, quality rules, and retention on every node; a thin map is `control-gap`, not ready.
- **A lineage is a DAG.** An orphan node, a dangling edge, or a cycle makes the graph unsound and
  keeps the package `draft-incomplete`.
- **Provenance is a versioned contract.** Record `spec_version` and each `source_id` so the
  lineage basis is reproducible and reviewable, and so governance approves a fixed artifact.
