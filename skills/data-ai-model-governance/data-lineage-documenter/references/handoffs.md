# Adjacent-Skill Handoffs — data-lineage-documenter

Documenting the lineage (this skill) is a **separate control activity** from investigating data
defects, assessing model/AI risk, analyzing a change, and approving or recording the lineage —
different entitlements, artifacts, and decisions. This skill emits a `spec_version`-keyed
**draft lineage document** with `governance_approval: pending`; it must not certify, attest,
decide, resolve an issue, or write a catalog/system-of-record record.

## Upstream (feeds this skill)

| Upstream skill | Provides | Handoff artifact |
| -------------- | -------- | ---------------- |
| `model-inventory-maintainer` | The inventory record, dependencies, materiality, and the pointer to the model/data product whose lineage is documented | `model_id`/product id + dependency list + criticality |
| `ai-use-case-intake-classifier` | Governance path + inherent risk/criticality that scope how much lineage documentation is required | product/use-case id + criticality |

## Downstream (this skill hands off to)

| Downstream skill | When | Handoff artifact |
| ---------------- | ---- | ---------------- |
| `data-quality-issue-investigator` | A node surfaces a data-quality defect (failed rule, reconciliation break) needing root-cause and remediation | node id + quality rule + observed defect |
| `model-risk-documenter` | The lineage feeds the model-risk / validation documentation pack's data-traceability section | approved lineage document + `spec_version` |
| `ai-risk-assessment-builder` | The lineage feeds the data, privacy, and third-party sections of the AI risk assessment | lineage document + node classifications + provenance |
| `model-change-impact-analyzer` | A proposed change alters source-to-output dependencies and needs impact/revalidation scoping | affected nodes/edges + downstream consumers |

## Specialist / adjacent (route out; do not do here)

| Skill | When |
| ----- | ---- |
| `agent-audit-trail-reviewer` | The pipeline is agentic and needs a reproducibility/control review of prompts, tool calls, and retained sources beyond naming the log node |

## Human / operations handoff (no catalog skill)

- **Recording the lineage in the data catalog** and **approving** the document are performed by
  the data-governance owner (Data Governance Office / Chief Data Office) and the accountable
  data steward — human, entitled roles operating the catalog. This skill drafts only and never
  writes the catalog record.

## Duplicate-execution prevention

- This skill **does not** investigate data-quality issues, assess model/AI risk, analyze change
  impact, or record/approve the lineage — those belong to the routes above or to a human owner.
- Governance approval is a **human** gate; the document is never self-approved and never written
  back to the catalog until an owner and steward sign off.
- A `needs-data` / `undocumented-transform` element is resolved by a human supplying the source,
  owner, or transformation — never by inventing one here.
