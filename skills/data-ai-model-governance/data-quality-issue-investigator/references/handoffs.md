# Adjacent-Skill Handoffs — data-quality-issue-investigator

Detection/monitoring (which populates the issue queue), **investigation** (this skill), and
substantive **remediation/closure** are separate control activities with different
entitlements, evidence depth, and case states. This skill emits a durable `case_id` +
evidence bundle and routes; it never remediates or closes.

## Downstream / lateral (this skill routes to)

| Skill | When | Handoff artifact |
| ----- | ---- | ---------------- |
| `data-lineage-documenter` | Root cause is suspected upstream and the transformation chain must be traced/documented (`recommend-upstream-trace`) | `case_id` + defect profile + affected dataset/field |
| `ai-incident-investigator` | The defect materially affects a model, a regulated decision, or a regulatory report (`recommend-incident-escalation`) | `case_id` + evidence bundle + affected consumers |
| `model-change-impact-analyzer` | A model/pipeline change is the suspected cause and its revalidation impact must be assessed | `case_id` + change reference + affected model(s) |
| `model-inventory-maintainer` | An affected model's inventory record (data dependency, status) needs updating | `case_id` + affected model id(s) + evidence |

## Upstream (feeds this skill)

A read-only data-quality monitor or profiling job produces the raw issue queue. That
detection step is **not** part of this skill (`aws-fsi-scheduled-agent: no`); a monitor may
enrich, threshold, and queue but must not investigate, decide, or close.

## Human / operations handoffs (no catalog skill)

- **Remediation** of the defect (data fix, backfill, rule change) is performed by the **data
  owner / remediation team** — a human/operations hand-off, not a skill.
- **Issue closure, root-cause confirmation, and waivers** belong to the **data-governance
  owner / issue-management process** under `required` human approval.
- A defect implicating **licensed regulatory reporting** (e.g., a filed regulatory return) is
  raised to the **regulatory-reporting control owner**; this skill never files or corrects a
  filing.

## Duplicate-execution prevention

- This skill **does not** document lineage, investigate model/agent incidents, assess change
  impact, or remediate — those belong to the skills or humans above.
- The downstream owner consumes the `case_id`/bundle rather than re-investigating.
- A `possible-duplicate` link is resolved by a human, not auto-merged or auto-closed here.
