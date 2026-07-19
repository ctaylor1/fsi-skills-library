# Source Map — model-change-impact-analyzer

## Source hierarchy (highest first)

| Rank | Source (MCP integration) | Used for | Access |
| ---- | ------------------------ | -------- | ------ |
| 1 | **Model registry** (record of approved state) | Current model version, materiality, approvals, lifecycle, dependencies | Read-only |
| 2 | **Change record** (proposed delta) | Per-dimension before/after, risk flags, requested deploy | Read-only |
| 3 | **Policy / controls library** (versioned) | Control baselines, decisioning/fair-lending standards, revalidation policy | Read-only |
| 4 | **Evaluation harness** | Testing/benchmark baselines and coverage | Read-only |
| 5 | **Data catalog / lineage** | Data source provenance, quality rules, retention | Read-only |
| 6 | **Agent / tool logs** (for agents) | Current tool set, permissions, guardrails | Read-only |
| 7 | Change-impact **config** (versioned) | Banding thresholds and scope/governance mapping | Read-only |

Never substitute the requester's assertion for the registry, policy, or evaluation record.
If the registry and the change record conflict, cite both and flag for the adjudicator.

## Citation format

`{system}:{ref}@{date}` — e.g. `registry:MDL-00731;field=training_data@2026-07-10` or
`policy:credit-decisioning-standard;sec=4.2@2026-06-01`. Every fired dimension cites the
specific before/after evidence and the source ref behind it.

## Freshness / effective dates

- Banding config (thresholds, scope/governance mapping) is a **versioned contract**; the
  output records the config version used so an assessment is reproducible.
- Each fired dimension's evidence carries the source ref's effective date.
- The change record's `target_deploy` is informational only; it never shortens the required
  revalidation or human adjudication.

## Least-privilege operations (deployment)

- `registry.get(model_id, version)` → current approved model attributes + materiality.
- `change.get(change_id)` → the proposed change record (bounded delta).
- `policy.get(standard, version)` → control/decisioning/fair-lending baselines.
- `evalharness.coverage(model_id)` → current test suites + acceptance thresholds.
- `catalog.lineage(dataset)` → provenance, quality rules, retention.
- `config.get('mcia', version)` → banding thresholds + scope/governance mapping.

All read-only, deterministic, durable `assessment_id`, below the fixed timeout; page long
registries/logs as resumable stages. No mutating operation exists in this skill.
