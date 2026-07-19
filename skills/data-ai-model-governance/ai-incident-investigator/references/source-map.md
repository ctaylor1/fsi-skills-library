# Source Map — ai-incident-investigator

## Source hierarchy (highest first)

| Rank | Source (MCP integration) | Used for | Access |
| ---- | ------------------------ | -------- | ------ |
| 1 | **Risk / issue management** | Incident record + state (system of record), `case_id`, linkage | Read-only |
| 2 | **Model registry** | Implicated model/agent identity, version, owner, deployment context | Read-only |
| 3 | **Agent / tool logs** | What the agent did: prompts, tool calls, outputs, timestamps (chronology + chain of custody) | Read-only |
| 4 | **Evaluation harness** | Behavioral evidence: eval/monitor runs, fairness/quality signals | Read-only |
| 5 | **Data catalog / lineage** | Affected-data classification, lineage, upstream defect context | Read-only |
| 6 | **Policy library** | AI/model-risk policy, incident taxonomy, notification thresholds | Read-only |
| 7 | Severity + routing **config** (versioned) | Deterministic severity scoring and remediation routing | Read-only |

## Citation format

`{system}:{ref}@{date/version}` — e.g. `issue:INC-4471@2026-07-14`,
`modelreg:model=M-27@v3.1`, `agentlog:trace=TR-88@2026-07-11`,
`evalharness:run=EVAL-556@2026-07-05`, `config:ai-gov-severity@ai-gov-2026.07`.

## Freshness / effective dates

- Incident state must be read fresh from the risk/issue system (avoid working an incident a
  human has already re-scoped or escalated).
- Agent/tool logs and eval runs are **chain-of-custody evidence** — capture and cite them
  before they roll off; note the retrieval time.
- Severity and routing use a **versioned** config; the version is recorded on every case for
  reproducibility and review.

## Least-privilege operations (deployment)

- `issues.read(incident_id)`, `issues.find(model_ref, window)` (linkage) — read-only.
- `modelreg.get(model_ref, version)` — read-only identity/owner resolution.
- `agentlog.read(trace_id | session)`, `evalharness.read(run_id)` — read-only, bounded.
- `catalog.lineage(dataset)`, `policy.get(...)`, `config.get('ai-gov-severity'|'ai-gov-routing', version)` — read-only.

No mutation from this skill. It makes **no** state change: closure, determination, routing
acceptance, and notification are proposals a human owner executes via the approval broker.
