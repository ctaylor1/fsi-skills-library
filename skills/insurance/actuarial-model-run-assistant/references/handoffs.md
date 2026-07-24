# Adjacent-Skill Handoffs — actuarial-model-run-assistant

Produces a reproducible loss-development run packet (`run_id`) and stops. It does not book
reserves or make reserving decisions.

## Downstream (route the human/reviewer to)
| Downstream skill | When | Handoff artifact |
| ---------------- | ---- | ---------------- |
| `actuarial-data-lineage-checker` | Triangle data provenance/consistency is questioned | triangle id + suspect cells |
| `insurance-regulatory-filing-packager` | The run supports a rate filing exhibit | run id + indicated change |

## Upstream (may call this skill)
Reserving and pricing workflows may request a development run. This skill is interactive
(`aws-fsi-scheduled-agent: no`).

## Duplicate-execution prevention
- This skill only **runs the documented method and reports an indication**; it never books,
  sets, or certifies a reserve — those belong to the qualified actuary.
- Downstream reuses the `run_id` indication rather than recomputing.
