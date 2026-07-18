# Source Map — ai-evaluation-benchmark-builder

## Source hierarchy (highest first)

| Rank | Source (MCP integration) | Used for | Access |
| ---- | ------------------------ | -------- | ------ |
| 1 | **Model registry** | System-under-eval identity, version, use case, inherent risk rating, prior model card | Read-only |
| 2 | **Policy / regulatory library** (controlled content) | Approved acceptance thresholds, evaluation standard, SR 11-7 benchmarking expectations | Read-only |
| 3 | **Risk appetite / risk & issue systems** | Approved tolerances used as thresholds; open issues affecting scope | Read-only |
| 4 | **Data catalog** | Representative evaluation datasets (task, trigger, regression, safety, robustness) + lineage | Read-only |
| 5 | **Evaluation harness** | Available metrics, run configs, prior baselines (methodology, not live execution) | Read-only |
| 6 | **Agent / tool logs** | Representative traffic mix, latency/cost profiles, trigger/routing behavior | Read-only |
| 7 | **Prior model card / baseline** | Prior-version baselines for regression and drift framing | Read-only |

Precedence: an **approved threshold** in policy or the risk appetite statement outranks any
value inferred from logs or a prior baseline. Where they conflict, cite both and flag the
threshold `proposed` (needs-calibration) for governance to resolve — never silently pick one.

## Citation format

`{system}:{ref}@{version}` — e.g. `registry:MDL-4821@v2.3.0-rc1`,
`source:POL-AI-01#threshold`, `data-catalog:onboarding-task-suite-v3`,
`source:MC-PRIORV#baseline`. Record `spec_version` (the evaluation methodology / threshold
catalog version) on every package.

## Freshness / effective dates

- Read the **current** model version and its inherent risk rating fresh; a benchmark built
  against a superseded version or stale risk rating is invalid.
- Thresholds and baselines are a **versioned contract**: record the `source_id` and
  `spec_version` so the acceptance basis is reproducible and reviewable.
- `as_of_date` frames latency/cost/traffic profiles drawn from logs.

## Least-privilege operations (deployment)

- `registry.get(model_id, version)` → identity, risk rating, prior model card — read-only.
- `policy.get(source_id)`, `risk_appetite.get(source_id)` → approved thresholds — read-only.
- `catalog.find(dataset_ref)` → dataset existence, lineage, representativeness metadata —
  read-only.
- `harness.metrics()` / `logs.profile(window)` → available metrics and traffic/latency/cost
  profiles — read-only.

No mutation from this skill. It **never** invokes the harness to run an evaluation, writes to
the model registry, or records a governance decision. The drafted benchmark is a proposal
emitted for the model-risk-governance reviewer via the approval broker.
