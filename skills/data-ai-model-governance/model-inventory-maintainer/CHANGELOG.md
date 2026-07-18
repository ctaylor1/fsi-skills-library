# Changelog — model-inventory-maintainer

## [0.1.0] — 2026-07-17
Initial authoring in the FSI Skills Library (baseline status: `new`).

- **Scope:** create/update model and agent inventory records — ownership, purpose, lineage,
  materiality tier, dependencies, versions, approvals, lifecycle status — as a PROPOSED
  change proposal for human adjudication. Read-only; no posting, approval, or closure.
- **Deterministic computation:** required-attribute completeness; a versioned **materiality
  tie-out** (four factors → Tier 1/2/3, single high factor escalates); **lifecycle-transition**
  validity against a documented state machine; **source reconciliation** with a typed break
  taxonomy (`value_mismatch` / `missing_in_inventory` / `missing_in_source` / `stale`); and
  findings, each with cited evidence (see `scripts/calculate_or_transform.py`).
- **Controls:** R3; hard boundary against autonomous decision, system-of-record posting,
  approval/attestation/certification, and finding closure/filing; versioned-config
  thresholds only; `requires_adjudication` gate; `required` human approval.
- **Scripts:** `validate_input` (change-request schema, factor ranges, completeness
  warnings), the compute engine, `validate_output` (status/adjudication gate, materiality
  tie-out, finding-citation traceability, break-typing, no-decision language screen,
  disclaimer).
- **Evaluations:** trigger/routing, golden Tier 1 update case, create-without-registry edge,
  deterministic script checks, no-autonomous-decision safety + injection, adjudication
  authorization.
- **Handoffs:** upstream from `ai-use-case-intake-classifier`, `ai-risk-assessment-builder`,
  `model-change-impact-analyzer`; downstream to `model-validation-assistant`,
  `model-risk-documenter`, `data-lineage-documenter`, `agent-permission-scope-reviewer`,
  `agent-audit-trail-reviewer`.

### Pending before release
- Domain SME (model risk) + control-owner blind review; confirm the versioned materiality
  rubric, lifecycle map, and staleness window and their owner.
- Confirm the required-attribute standard against the firm's model-inventory policy.
- Wire read-only MCP integrations (registry, catalog, eval harness, agent logs, policy,
  risk/issue tracker) at deployment.
