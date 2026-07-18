# Build Archetypes

Each skill is assigned one of nine build archetypes (`aws-fsi-archetype`) with an
associated agent pattern (`aws-fsi-agent-pattern`). The archetype drives which package
components are mandatory and what the primary validation focus is.

| Archetype | Agent pattern | What it does | Mandatory package emphasis |
| --------- | ------------- | ------------ | -------------------------- |
| **Explain & summarize** | Interactive decision-support copilot | Turn authoritative sources into plain-language explanations/summaries with citations. | `source-map.md`; citation-coverage evals; prohibited-advice checks. |
| **Analyze & review** | Interactive decision-support copilot | Apply rules/calculations to inputs, surface findings and exceptions, cite evidence. | `validate_input`, `validate_output`; false-positive/negative fixtures. |
| **Model & calculate** | Interactive production copilot | Build source-linked models/forecasts with drivers, scenarios, and tie-outs. | `calculate_or_transform`; formula/tie-out unit tests; reproducibility. |
| **Draft & package** | Interactive production copilot | Assemble a controlled deliverable (memo, pack, response, register) from approved inputs. | `assets/output-template.*`; template fidelity; unsupported-assertion checks. |
| **Reconcile & validate** | Interactive production copilot | Match records across sources, classify breaks, preserve lineage, propose corrections. | `calculate_or_transform` (matching); tie-outs; break taxonomy; idempotency. |
| **Monitor & alert** | Scheduled monitor + human queue | Read-only scheduled monitoring against thresholds; raise alerts / queue items. | `controls.md` (no autonomous action); freshness, dedup, escalation latency. |
| **Investigate & casework** | Case agent + evidence bundle | Build an evidence bundle, chronology, and disposition recommendation for a case. | `controls.md`, `handoffs.md`; durable case IDs; **no autonomous closure**. |
| **Domain workflow** | Interactive decision-support copilot | A multi-step domain procedure that doesn't fit a single narrower archetype. | Task completion, control adherence, reviewer acceptance. |
| **Orchestrate & resolve** | Plan-validate-execute workflow agent | Plan a change, validate it, gate on approval, execute idempotently, verify, audit (R4). | `controls.md`, `handoffs.md`, `validate_input`/`validate_output`; rollback + audit-log. |

There is one specialized pattern outside the nine: **Skill engineering copilot**
(`fsi-skill-authoring-assistant`), which authors and validates other skills.

## Archetype → skill type

Each skill also carries a coarse `aws-fsi-skill-type` (one of six). The default is derived
from the archetype; a curated override set handles content-specific cases. See
[METADATA-SCHEMA.md](METADATA-SCHEMA.md#skill-type-aws-fsi-skill-type).

| Archetype (default) | Skill type |
| ------------------- | ---------- |
| Draft & package, Model & calculate | Artifact-creation skills |
| Analyze & review, Reconcile & validate, Investigate & casework | Analysis and evaluation skills |
| Explain & summarize, Domain workflow | Guidance or domain-expertise skills |
| Monitor & alert | System-interaction or operational skills |
| Orchestrate & resolve | Workflow or orchestration skills |
| (overrides) message/data transformers, skill-authoring | Utility skills |

## Triage vs. investigation

Several domains split first-line **triage** (high volume, prioritize, resolve basic data
issues, package escalations) from substantive **investigation** (deep evidence, chronology,
disposition). These are distinct skills with distinct entitlements and case states, and
must route to each other via `handoffs.md`. Neither closes substantive cases autonomously.
Examples:

- `surveillance-alert-triager` → `market-surveillance-alert-investigator`
- `aml-alert-triager` → `transaction-monitoring-alert-investigator` → `suspicious-activity-report-drafter`
- `payment-failure-diagnoser` / `iso-20022-message-interpreter` → `payment-exception-investigator` → `payment-repair-assistant`

## Scheduled-agent posture

Only **Monitor & alert** skills may run as scheduled agents, and only in read-only
`alert-only` mode (`aws-fsi-scheduled-agent: read-only-monitoring`). All other skills
declare `no`. A scheduled monitor may enrich, threshold, deduplicate, and queue — it may
never act, decide, or close.
