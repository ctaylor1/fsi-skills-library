# Source Map — model-inventory-maintainer

## Source hierarchy (highest first)

| Rank | Source (MCP integration) | Authoritative for | Access |
| ---- | ------------------------ | ----------------- | ------ |
| 1 | **Model registry** (position of record) | Model/agent identity, version, owner, lifecycle status, registration | Read-only |
| 2 | **Data catalog** | Lineage, upstream datasets, features, data classification | Read-only |
| 3 | **Evaluation harness** | Performance/eval evidence, benchmark runs, eval status | Read-only |
| 4 | **Agent / tool logs** | Agent capabilities, tool scope, permissions actually exercised | Read-only |
| 5 | **Policy retrieval** | Materiality rubric, lifecycle policy, required-attribute standard | Read-only |
| 6 | Governance **config** (versioned) | Materiality thresholds, allowed lifecycle transitions, staleness window | Read-only |
| 7 | **Risk / issue tracker** | Linked issues, findings, remediation status | Read-only |

The inventory is a **derived** record. Never substitute the proposed record for a source of
record: if the proposed record and the registry/catalog conflict, record the break and cite
both; do not silently overwrite either side.

## Citation format

`{system}:{ref}@{date}` — e.g. `registry:model=MOD-4471;ver=3.2@2026-07-10`,
`catalog:dataset=credit_bureau_v4@2026-06-30`, `eval:run=EVAL-8891@2026-07-05`. Every
proposed attribute and every finding cites the specific source rows and the snapshot dates
used, plus the rubric/config version for computed values (`rubric:inv-rubric-2026.07#...`).

## Freshness / effective dates

- The materiality rubric and lifecycle transition map are a **versioned contract**; the
  output records the `config_version` so a proposal is reproducible.
- Source snapshots carry a snapshot date; snapshots older than the configured staleness
  window (default 90 days) are flagged `stale` and cited with both dates.
- The proposal `as_of` bounds the comparison; do not mix snapshots from different runs
  without recording it.

## Least-privilege operations (deployment)

- `registry.get(record_id)` → identity, version, owner, lifecycle status (read-only).
- `catalog.lineage(record_id)` → datasets, features, classifications (read-only).
- `eval.results(record_id)` → latest eval run + status (read-only).
- `agentlog.scope(record_id)` → declared tools/permissions for agents (read-only).
- `policy.get('model-inventory', version)` → required-attribute standard + rubric.
- `config.get('inv-rubric', version)` → materiality thresholds + lifecycle map + staleness.
- `issues.linked(record_id)` → open findings/issues (read-only).

All read-only and deterministic, keyed to a durable `proposal_id`, kept below the fixed
timeout; page large lineage/eval histories as resumable stages. No operation writes to the
inventory, registry, or issue tracker — posting and adjudication are human steps.
