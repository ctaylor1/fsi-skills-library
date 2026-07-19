# Changelog — data-lineage-documenter

## [0.1.0] — 2026-07-17
Initial authoring in the FSI Skills Library (baseline status: `new`). Created to separate
data-lineage *documentation* from data-quality investigation, model-risk documentation, and
catalog recording (distinct entitlements, artifacts, and decisions).

- **Scope:** draft a source-linked lineage document for a data product / model-feature pipeline —
  every source-to-output node with its owner, classification, controls, quality rules, and
  retention, and every dependency edge with its transformation, each traced to an authoritative
  source — plus graph-integrity checks and a criticality-scaled coverage matrix. Draft-only; the
  document is a proposal for data-governance review.
- **Controls:** R3; no certification/attestation, no accuracy or regulatory-fitness (BCBS 239)
  determination, no self-approval, no invented source; untraced elements are `needs-data` /
  `undocumented-transform`; `governance_approval` stays `pending`; no write to the data catalog or
  any system of record; versioned lineage methodology/catalog (`spec_version`).
- **Scripts:** `validate_input` (request schema, provenance/coverage/graph warnings), lineage
  builder (`calculate_or_transform`: provenance resolution + required-attribute check by
  criticality + orphan/dangling/cycle detection + status assignment + coverage matrix),
  `validate_output` (template fidelity, traced-only for ready elements, graph & coverage
  integrity, required approvals, certification/attestation/write language screen, standing note).
- **Assets:** `assets/output-template.md` (the drafted lineage document for data-governance review).
- **Evaluations:** trigger/routing, golden 10-node / 9-edge request exercising every node and edge
  status, deterministic script checks, a non-compliant-document safety fixture (unknown layer,
  untraced-but-traced-marked provenance, self-approval, certification/write language, missing
  standing note), no-certify / no-invented-source refusals, and a self-approval authorization refusal.
- **Handoffs:** upstream `model-inventory-maintainer`, `ai-use-case-intake-classifier`;
  downstream `data-quality-issue-investigator`, `model-risk-documenter`, `ai-risk-assessment-builder`,
  `model-change-impact-analyzer`; adjacent `agent-audit-trail-reviewer`; catalog recording and
  approval are a human data-governance owner / data steward action (no catalog skill).

### Pending before release
- AI/Model Risk Governance + Data Governance Office control-owner review of the required-attribute
  and graph-integrity rules.
- Confirm the approved data-lineage methodology + catalog source, owner, and versioning
  (`spec_version`), and the required-node-attributes-by-criticality table.
- Wire read-only MCP integrations (data catalog, model registry, policy/data-management standard,
  data contracts, agent/tool logs, risk/issue systems) at deployment.
