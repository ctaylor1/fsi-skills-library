# Adjacent-Skill Handoffs — actuarial-data-lineage-checker

Produces a break/lineage packet (`lineage_id`) and stops. It does not correct data, select
assumptions, or run models.

## Downstream (route the human to)
| Downstream skill | When |
| ---------------- | ---- |
| `actuarial-model-run-assistant` | Data is clean/approved and the model should be run on it |
| `reserving-analysis-assistant` | Reserve development / severity / frequency analysis |

## Upstream (may call this skill)
Actuarial data-prep workflows request a lineage/break packet before a run. Interactive
(`aws-fsi-scheduled-agent: no`).

## Duplicate-execution prevention
- This skill **reconciles and evidences breaks only**; it never corrects data, selects
  assumptions, runs models, or certifies reserves — those belong to the data owner, the
  actuary, and `actuarial-model-run-assistant` / `reserving-analysis-assistant`.
- Downstream reuses the `lineage_id` evidence rather than re-reconciling.
