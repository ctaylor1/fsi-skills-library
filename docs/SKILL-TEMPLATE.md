# Reusable FSI `SKILL.md` Template (v2)

Copy this template to author a new skill. It makes adjacent-skill boundaries, routing,
effective dates, durable cases, and stale-source handling explicit. Keep the body under
**500 lines**; move detail into `references/` files (one level deep). See
[METADATA-SCHEMA.md](METADATA-SCHEMA.md) for field values.

## Frontmatter

```yaml
---
name: <skill-name>                     # must equal the directory name
description: >-
  <What the skill does and when it should activate; include specific user intents,
  artifacts, and domain keywords. Also state the hard boundary (what it never does).>
license: MIT
compatibility: Amazon Quick Desktop; requires <named MCP integrations, local tools, packages, network>.
metadata:
  aws-fsi-category: "<category>"
  aws-fsi-skill-type: "<one of the six skill types>"
  aws-fsi-risk-tier: "<R1|R2|R3|R4>"
  aws-fsi-archetype: "<archetype>"
  aws-fsi-agent-pattern: "<agent pattern>"
  aws-fsi-delivery-wave: "<wave>"
  aws-fsi-action-mode: "<action mode>"
  aws-fsi-scheduled-agent: "<no|read-only-monitoring>"
  aws-fsi-baseline-status: "<new|existing-updated|existing-no-changes>"
  aws-fsi-human-approval: "<none|external-delivery|required>"
  aws-fsi-data-classification: "<classification>"
  aws-fsi-jurisdictions: "<configured jurisdictions>"
  aws-fsi-owner: "<business owner>"
  aws-fsi-primary-user: "<primary user role(s)>"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "<yyyy-mm-dd>"
---
```

## Body sections (required)

| Section | Required content |
| ------- | ---------------- |
| **Purpose and outcome** | The exact repeatable task, intended user, business outcome, and what a successful output enables. |
| **Use when** | Positive trigger intents, artifacts, synonyms, and situations that should activate the skill. |
| **Do not use** | Adjacent tasks, prohibited decisions, unsupported jurisdictions, and conditions requiring another skill or a specialist. |
| **Adjacent-skill handoffs** | Upstream/downstream skills, routing criteria, required handoff artifacts, durable case IDs, and how duplicate execution is prevented. |
| **Inputs and prerequisites** | Required files, data fields, permissions, systems, confirmations, freshness/effective dates, and data-quality minimums. |
| **Source hierarchy** | Ranked authoritative systems/documents; require citations, dates, versions, owners, and conflict handling. |
| **Workflow** | Concise ordered steps with decision points and case-state transitions; load references only when triggered. |
| **Validation loop** | Do the work, run deterministic checks or a reference checklist, correct failures, repeat until pass or fail closed. |
| **Human approval** | Every decision, closure, filing, trade, payment, journal, commitment, or system write requiring authorization. |
| **Failure handling** | Missing data, ambiguous identity, stale/conflicting sources, tool timeout, no retry, permission denial, partial completion. |
| **Output contract** | Structure, templates, calculations, citations, uncertainty, assumptions, case/handoff artifacts, machine-readable outputs. |
| **Privacy and records** | Data minimization, redaction, access, retention, records, logging, and deletion requirements. |
| **Gotchas** | Concrete domain/system traps discovered from real executions; keep the highest-value warnings here. |

## Evaluation pack (author alongside the skill)

| Layer | Minimum requirement |
| ----- | ------------------- |
| **Trigger & routing tests** | Positive and negative queries for this skill and adjacent skills; measure activation and handoff precision/recall. |
| **Golden task fixtures** | Normal, edge, stale-source, failure, cross-skill, and high-risk cases with expected outputs and assertions. |
| **With/without benchmark** | Compare with no skill and the prior version for quality, time, tool/token cost, and blind reviewer preference. |
| **Deterministic tests** | Unit tests for extraction, spreading, formulas, schemas, clause comparison, reconciliation, thresholds, redaction, idempotency. |
| **Safety & authorization** | Prompt injection, exfiltration, overreach, prohibited decision/action, case closure, role/permission, approval-bypass attempts. |
| **Human acceptance** | Blind domain-SME review, control-owner review, legal/compliance/model-risk where applicable, accessibility review. |
| **Production telemetry** | Activation, wrong-skill activation, handoff success, completion, corrections, overrides, unsafe blocks, latency, cost, exceptions. |

## MCP & Amazon Quick design rules (enforce in `scripts/` and `source-map.md`)

- Small deterministic tools with explicit JSON schemas and durable case/job IDs.
- Keep operations below the fixed timeout; split long work into resumable stages.
- Separate read, triage, investigate, draft, authorize, execute, verify, close, report.
- Default to Read Only or Ask Each Time; mutating tools need idempotency, validation,
  verification, and rollback guidance.
- Do not assume automatic retries or step-up authorization.
- Treat registered operations and rule/content sources as versioned contracts.
- Restrict scheduled agents to read-only monitoring, freshness checks, briefing, or queue
  creation.
