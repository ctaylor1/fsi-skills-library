# Source Map — prompt-and-agent-risk-reviewer

## Source hierarchy (highest first)

| Rank | Source (MCP integration) | Used for | Access |
| ---- | ------------------------ | -------- | ------ |
| 1 | **Agent/prompt specification** (registered config: system prompt, tools, memory, retrieval, guardrails, failure modes) | The object under review | Read-only |
| 2 | **Control catalog / AI policy** (versioned) | The control checklist, severities, and rating/disposition mapping | Read-only |
| 3 | **Model registry & data catalog** | Data classification, model/use-case linkage, ownership | Read-only |
| 4 | **Agent/tool logs & evaluation harness** | Whether logging/eval coverage is actually wired | Read-only |
| 5 | **Risk & issue systems** | Prior findings, open issues, and where recommendations are routed | Read-only |

The registered agent specification is the object of record. If the spec and a design
document or ticket conflict, cite both and flag for the reviewer — never assume an
undocumented control is present. Missing/undocumented control blocks are treated as
controls-not-evidenced and surfaced in `data_gaps`.

## Citation format

`agentspec:{agent_id}#{locus}@{as_of}` — e.g.
`agentspec:collections-outreach-agent#tools[email.send]@2026-07-15`. Every fired finding
cites the exact configuration locus (tool, guardrail flag, memory block, prompt attribute)
that triggered it.

## Freshness / effective dates

- The **control catalog** (checklist, severities, rating/disposition mapping) is a
  **versioned contract**; the output records `control_catalog_version` so a review is
  reproducible.
- `as_of` pins the review to the exact spec revision reviewed; re-running against the same
  spec and catalog reproduces the findings, rating, and disposition.
- Re-review is required when the spec changes (new tool, new retrieval source, autonomy
  change) — route material changes to `model-change-impact-analyzer`.

## Least-privilege operations (deployment)

- `agentspec.get(agent_id, revision)` → the registered configuration under review.
- `controlcatalog.get('agent-controls', version)` → checklist + severities + mapping.
- `registry.get(agent_id)` → data classification, use-case linkage, owner.
- `logs.coverage(agent_id)` / `evalharness.coverage(agent_id)` → whether logging/eval exist.
- `issues.list(agent_id)` → prior findings / open issues.
All read-only, deterministic, durable `review_id`, below the fixed timeout; page long
tool/retrieval inventories as resumable stages. No write, deploy, approve, or close
operation is bound.
