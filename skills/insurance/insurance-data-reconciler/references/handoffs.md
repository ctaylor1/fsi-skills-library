# Adjacent-Skill Handoffs — insurance-data-reconciler

Produces a break/lineage packet (`lineage_id`) and stops. It does not correct data, select
assumptions, or run models.

## Downstream (route the human to)
| Downstream skill | When |
| ---------------- | ---- |
| `pc-reserving-analysis-assistant` | Data is clean/approved and the model should be run on it |
| `pc-reserving-analysis-assistant` | Reserve development / severity / frequency analysis |

## Upstream (may call this skill)
Actuarial data-prep workflows request a lineage/break packet before a run. Interactive
(`aws-fsi-scheduled-agent: no`).

## Duplicate-execution prevention
- This skill **reconciles and evidences breaks only**; it never corrects data, selects
  assumptions, runs models, or certifies reserves — those belong to the data owner, the
  actuary, and `pc-reserving-analysis-assistant` / `pc-reserving-analysis-assistant`.
- Downstream reuses the `lineage_id` evidence rather than re-reconciling.

## Typed receiver validation

Prepare native receiver input together with `make_handoff` from the bundled insurance contract. Preserve source artifact, object/context and unresolved issues. Invoke `validate_handoff` with the actual receiver input validator; a producer claim of passed validation is insufficient. The receiver separately assesses its domain prerequisites and carries any upstream partial state. This is content binding and schema validation, not permission to act.
