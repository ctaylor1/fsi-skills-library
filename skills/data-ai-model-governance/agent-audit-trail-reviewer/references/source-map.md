# Source Map — agent-audit-trail-reviewer

## Source hierarchy (highest first)

| Rank | Source (MCP integration) | Used for | Access |
| ---- | ------------------------ | -------- | ------ |
| 1 | **Agent/tool log** (event record of the run) | The run's prompts, retrievals, tool calls, approvals, overrides, outputs, retention | Read-only |
| 2 | **Model registry** | The agent/model record: registered model/prompt/config versions, materiality, owner, lifecycle status | Read-only |
| 3 | **Policy / control config** (versioned) | Allowed tools, required reproducibility fields, action classes requiring approval, required retained objects, disposition mapping | Read-only |
| 4 | **Data catalog / evaluation harness** | Resolving retrieved sources and referenced evaluations behind the run | Read-only |
| 5 | **Risk / issue register** | Read-only context on any existing issue for the agent (never written by this skill) | Read-only |

The **agent/tool log is the record of what happened**; the **registry and policy define what
should have happened**. Never substitute an assumption ("the approval probably happened") for
a log event. If the log and the registry/policy conflict, cite both and flag for the reviewer.

## Citation format

`trail:run={run_id};event={event_id}@{ts}` — e.g. `trail:run=R-771;event=E-005@2026-07-16T10:10:00`.
Header-level and object-level findings cite `trail:run={run_id}#header@{as_of}` and
`trail:run={run_id}#retention={object}@{as_of}`. Every finding cites the specific event(s)
and the policy/config expectation it deviates from.

## Input schema (JSON)

Top-level: `run_id`, `agent_id`, `as_of` (YYYY-MM-DD), `policy_version`, `run{...}`,
`config{...}`, `events[]`. See [../scripts/validate_input.py](../scripts/validate_input.py).

- `run{}` — `model_id`, `model_version`, `prompt_version`, `config_version`, `seed`,
  `temperature`, `started_at`, `ended_at`.
- `config{}` — `allowed_tools[]`, `required_repro_fields[]`,
  `approval_required_action_classes[]`, `required_retained_objects[]`.
- `events[]` — each `{event_id, type, ts, ...}` where `type` is one of
  `prompt | retrieval | tool_call | approval | override | output | retention`:
  - `retrieval` — `source_ref`, `citation`.
  - `tool_call` — `tool`, `operation`, `action_class` (`read|write|decision`),
    `approval_required`, `approval_event_id`.
  - `approval` — `for_event`, `approver`, `decision`.
  - `override` — `actor` (`human|agent|...`), `overrode`, `reason`.
  - `retention` — `object`, `retained`, `retention_class`.

## Freshness / effective dates

- Policy and control config are **versioned contracts**; the output records the
  `policy_version` used so a review is reproducible.
- The review evaluates a single run as of `as_of`; it does not aggregate across runs.

## Least-privilege operations (deployment)

- `agentlog.get(run_id)` → the run's ordered event trail (read-only, paged for long runs).
- `registry.get(agent_id|model_id)` → registered versions, owner, materiality.
- `policy.get('agent-audit', version)` → allowed tools, required fields, approval classes,
  retention objects, disposition mapping.
- `catalog.resolve(source_ref)` / `evalharness.get(eval_ref)` → resolve referenced sources.
- `issues.read(agent_id)` → existing issue context (read-only; never written here).

All read-only, deterministic, durable `review_id`, below the fixed timeout; page long trails
as resumable stages.
