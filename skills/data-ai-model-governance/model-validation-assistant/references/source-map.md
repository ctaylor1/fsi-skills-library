# Source Map — model-validation-assistant

## Source hierarchy (highest first)

| Rank | Source (MCP integration) | Used for | Access |
| ---- | ------------------------ | -------- | ------ |
| 1 | **Model risk framework / validation standard** (versioned) | The required validation areas, materiality/severity mapping, approver routing, template | Read-only |
| 2 | **Model registry / inventory** | System of record for the model, tier, owner, version, developer evidence, declared controls | Read-only |
| 3 | **Data catalog / lineage** | Training/inference data assets, provenance, quality profiling for the data area | Read-only |
| 4 | **Evaluation harness** | Independent performance, benchmark, robustness, and back-testing evidence | Read-only |
| 5 | **Agent / tool logs** | Autonomy, tool scope, and human-oversight evidence for agentic models | Read-only |
| 6 | **Policy / controlled-template library** | Approved validation-report template, standing disclaimer | Read-only |
| 7 | **Risk / issue-management system** | Existing open validation findings/issues to link (never to close) | Read-only |

Independent validation evidence outranks developer-attested claims. A `pass` supported only by
the model registry / developer materials (no independent `evidence_ref`) is **not** independent
evidence and earns no validation credit — it is surfaced as a coverage/independence gap. The
framework, materiality mapping, and template are a **versioned contract** (`framework_version`).

## Citation format

`{system}:{ref}@{date/version}` — e.g. `framework:mrm-2026.07`,
`modelreg:MODEL-778@v3`, `datacatalog:DS-4471@2026-07-08`,
`evalharness:benchmark-run=EV-220@2026-07-09`, `valwp:DQ-1@2026-07-10` (validation working
paper), `issue:CTRL-220@evidenced`.

## Freshness / effective dates

- The validation areas, materiality mapping, and approver routing are read from the **current**
  framework; a superseded standard can change the required areas or routing.
- Test/benchmark evidence must be current and tied to the model version under validation; stale
  or out-of-version evidence is treated as no independent evidence (no coverage credit).

## Least-privilege operations (deployment)

- `framework.get(version)` → required areas, materiality mapping, routing, template — read-only.
- `modelreg.get(model_ref)` / `modelreg.list_controls(model_ref)` — read-only.
- `datacatalog.get(asset_ref)` / `evalharness.get_run(run_ref)` — read-only, bounded.
- `agentlogs.read(model_ref, window)` — read-only.
- `templates.get('model-validation-report', version)` — read-only controlled content.
- `issues.find(model_ref)` — read-only (link existing findings; never create/close here).

No mutation from this skill. The governed model documentation pack is maintained separately by
`model-risk-documenter`, and the validation decision is recorded by an authorized human via the
risk/issue system **after** review and adjudication.
