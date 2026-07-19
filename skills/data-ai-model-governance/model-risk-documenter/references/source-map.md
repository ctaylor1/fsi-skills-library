# Source Map — model-risk-documenter

## Source hierarchy (highest first)

| Rank | Source (MCP integration) | Used for | Access |
| ---- | ------------------------ | -------- | ------ |
| 1 | **Model-risk framework / documentation template** (versioned) | The ten required sections, required coverage, approver routing, standing disclaimer | Read-only |
| 2 | **Model inventory / registry** | System of record for the model identity, tier/materiality, version, owner, lifecycle status | Read-only |
| 3 | **Development artifacts** (development doc, spec) | Purpose, methodology (conceptual soundness, assumptions), change history | Read-only |
| 4 | **Independent validation reports** | Performance/outcomes testing, limitations, validation findings | Read-only |
| 5 | **Data catalog / lineage** | Data inputs, provenance, and lineage for the data and traceability sections | Read-only |
| 6 | **Monitoring / MLOps evidence** | Ongoing-monitoring metrics, drift/alert configuration for the monitoring section | Read-only |
| 7 | **Controls register / approval memos** | Model controls, governance, and recorded approvals / sign-offs | Read-only |
| 8 | **Risk / issue-management system** | Existing open findings/issues to reflect (never to close) | Read-only |

The framework, documentation template, and required-coverage list are a **versioned contract**
(`template_version` / `framework_version`). Never assemble a pack against a superseded template;
record both versions on every pack.

## Citation format

`{artifact_type}:{artifact_id}@{version}` — e.g. `devdoc:DEV-DOC-4412@v4.2`,
`validation:VAL-4412@2026.Q2`, `lineage:LIN-4412@v3`, `approval:APR-MEMO-4412@2026-06-15`,
`template:model-doc@model-doc-tmpl-2026.05#monitoring`. A source artifact **without a version**
is untraceable and earns **no citation credit** — the section becomes a `gap`.

## Freshness / effective dates

- Read the model identity and tier fresh from the inventory; documenting a stale tier can
  mis-route the approvers.
- The documentation template and required-coverage list are read from the **current**
  framework; a superseded template can change the required sections, coverage, or routing.
- Validation and monitoring evidence must be current; a stale or missing artifact is treated as
  no evidence for that section (coverage / traceability is not credited).

## Least-privilege operations (deployment)

- `framework.get(template_version)` → required sections, coverage, routing, disclaimer — read-only.
- `modelreg.get(model_id)` / `modelreg.get_tier(model_id)` — read-only.
- `artifacts.get(artifact_ref)` (development doc, validation report, lineage, controls,
  monitoring, approval memo) — read-only, bounded.
- `issues.find(model_id)` — read-only (reflect existing open findings; never create/close here).

No mutation from this skill. The completed pack is filed and any approval/attestation recorded
by an authorized human via the governance system **after** review and adjudication.
