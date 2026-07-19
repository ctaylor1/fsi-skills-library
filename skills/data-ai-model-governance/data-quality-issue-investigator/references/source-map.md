# Source Map — data-quality-issue-investigator

## Source hierarchy (highest first)

| Rank | Source (MCP integration) | Used for | Access |
| ---- | ------------------------ | -------- | ------ |
| 1 | **Issue / case management** | Issue + case state (system of record), dedup, durable `case_id` | Read-only |
| 2 | **Data catalog** | Dataset/field resolution, owners, stewards, downstream consumers | Read-only |
| 3 | **Data-quality / profiling** | Failing counts, failure rate, defect type, rule results | Read-only |
| 4 | **Model registry** | Affected models + materiality (route material impact to incident) | Read-only |
| 5 | **Agent / tool logs** | Chronology events where a pipeline/agent produced or consumed the data | Read-only |
| 6 | **Severity config + policy** (versioned) | Severity scoring + escalation thresholds | Read-only |

## Citation format

`{system}:{ref}@{date/version}` — e.g. `catalog:issue=DQI-3001`,
`catalog:dqrun=RUN-5521@2026-07-14`, `catalog:report=RPT-FR-Y9C@2026-07-15`,
`config:dq-severity@v2026.06`.

## Freshness / effective dates

- Issue/case state must be read fresh so a defect already covered by an open case is linked
  as a `possible-duplicate`, never re-opened or re-investigated in parallel.
- Profiling counts must carry the DQ-run timestamp; consumer lists must carry the catalog
  version so the blast radius is reproducible.
- Severity uses a **versioned** config; the version is recorded on every case.

## Least-privilege operations (deployment)

- `issues.read(queue|issue_id)`, `cases.find(dataset, rule, period)` (dedup) — read-only.
- `catalog.resolve(dataset_id|field)`, `catalog.consumers(dataset_id)` — read-only.
- `dq.results(rule_id, period)` → failing/total counts + defect type — read-only.
- `registry.model(model_id)` → materiality — read-only, no adjudication.
- `config.get('dq-severity', version)` — read-only.

No mutation from this skill. A remediation, incident, or closure is a **proposal** recorded
via the approval broker for a human owner; this skill writes no system of record.
