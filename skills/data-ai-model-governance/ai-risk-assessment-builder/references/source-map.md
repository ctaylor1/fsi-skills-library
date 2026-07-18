# Source Map — ai-risk-assessment-builder

## Source hierarchy (highest first)

| Rank | Source (MCP integration) | Used for | Access |
| ---- | ------------------------ | -------- | ------ |
| 1 | **Control framework / risk-domain taxonomy** (versioned) | The ten required domains, the likelihood x impact matrix, coverage bands, approver routing | Read-only |
| 2 | **Model registry** | System of record for the model/system, owner, version, declared controls, lifecycle stage | Read-only |
| 3 | **Data catalog / lineage** | Training/inference data assets, classification, provenance for the data domain | Read-only |
| 4 | **Evaluation harness** | Fairness, performance, robustness, and safety evidence for model/fairness/resilience domains | Read-only |
| 5 | **Agent / tool logs** | Autonomy, tool scope, and human-oversight evidence for agentic use cases | Read-only |
| 6 | **Policy / controlled-template library** | Approved assessment template, control catalog, standing disclaimer | Read-only |
| 7 | **Risk / issue-management system** | Existing open findings/issues to link (never to close) | Read-only |

The framework, matrix, and control catalog are a **versioned contract** (`framework_version`).
Never score against a superseded taxonomy; record the version on every pack.

## Citation format

`{system}:{ref}@{date/version}` — e.g. `framework:ai-rmf-2026.07`,
`modelreg:MODEL-778@v3`, `datacatalog:DS-4471@2026-07-11`,
`evalharness:fairness-run=EV-220@2026-07-09`, `issue:RISK-5521@open`.

## Freshness / effective dates

- The domain taxonomy and matrix are read from the **current** framework; a superseded
  framework can change the required domains, the matrix, or the approver routing.
- Control evidence must be current; a stale or missing evaluation is treated as no evidence
  for that control (coverage is not raised).

## Least-privilege operations (deployment)

- `framework.get(version)` → required domains, matrix, coverage bands, routing — read-only.
- `modelreg.get(model_ref)` / `modelreg.list_controls(model_ref)` — read-only.
- `datacatalog.get(asset_ref)` / `evalharness.get_run(run_ref)` — read-only, bounded.
- `agentlogs.read(system_ref, window)` — read-only.
- `templates.get('ai-risk-assessment', version)` — read-only controlled content.
- `issues.find(system_ref)` — read-only (link existing findings; never create/close here).

No mutation from this skill. The completed pack is filed and the risk decision recorded by an
authorized human via the risk/issue system **after** review and adjudication.
