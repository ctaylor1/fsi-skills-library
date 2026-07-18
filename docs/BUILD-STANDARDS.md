# Standards-Based Build Lifecycle (v2)

Every skill in this library is authored, validated, and operated through the common
delivery process below. It adds adjacent-skill routing, triage/investigation separation,
stale-content controls, durable case IDs, and specialized deterministic validation on top
of the [Agent Skills specification](https://agentskills.io/specification) and
[authoring best practices](https://agentskills.io/skill-creation/best-practices).

## Control model (risk tiers)

| Tier | Meaning |
| ---- | ------- |
| **R1 — informational** | Source-grounded explanations and summaries. |
| **R2 — analytical / drafting** | Models, analyses, reconciliations, and deliverables; **no binding decision**. |
| **R3 — regulated / control decision support** | Evidence and recommendations with **mandatory human adjudication**. |
| **R4 — approval-gated action** | plan → validate → approve → execute → verify → audit. |

See [RISK-TIERS.md](RISK-TIERS.md) for action modes and approval mapping.

## v2 requirements (apply to every skill)

- **Separate triage from investigation** and test routing in both directions.
- Add explicit **handoff artifacts** and **durable case identifiers**.
- Apply **effective-date and stale-language controls** to rules, forms, and approved content.
- **Fail closed** when package completeness, identity, source, version, or authorization
  is uncertain.

## Lifecycle stages

0. **Portfolio governance** — Establish skill owner, domain SME, risk owner, data owner,
   jurisdiction pack, risk tier, success metric, adjacent-skill boundaries, and retirement
   criteria before authoring.
1. **Task discovery** — Capture real artifacts, source systems, current procedure, expert
   decisions, handoffs, failure cases, exceptions, control evidence, and representative
   inputs and outputs.
2. **Skill contract** — Define user intent, positive and negative triggers, non-goals,
   input/output contracts, source hierarchy, freshness rules, action boundary, approvals,
   records, and upstream/downstream skill handoffs.
3. **Architecture and tools** — Choose read-only, draft-only, or approval-gated tools;
   design MCP operations for least privilege, deterministic schemas, idempotency, bounded
   payloads, sub-timeout execution, and durable case identifiers.
4. **Author SKILL.md** — Specification-valid frontmatter and concise instructions: use
   when, do not use, prerequisites, workflow, handoffs, validation, human approval,
   failure handling, output format, privacy, records, and gotchas.
5. **Bundle resources** — Add references for domain rules, source maps, data dictionaries,
   jurisdiction overlays, and adjacent-skill boundaries; add assets for approved templates
   and scripts for deterministic work.
6. **Build evaluations** — Trigger and routing tests, task-quality, regression, robustness,
   privacy, security, prompt-injection, authorization, stale-source, latency, cost, and
   human-review evaluations.
7. **Validate and review** — Run specification validation, script unit tests, golden-file
   checks, with/without benchmarks, domain SME review, control review, legal/compliance
   review, accessibility, and separation-of-duty review.
8. **Pilot and harden** — Pilot with bounded users and read-only or draft-only
   permissions; capture traces, corrections, false positives/negatives, wrong-skill
   activations, handoff failures, overrides, and missing gotchas.
9. **Release and operate** — Version, sign, publish through a governed catalog, assign
   role-based permissions, monitor activation and outcomes, recertify sources/rules/tools,
   support rollback, and retire stale or overlapping skills.

## Skill package components

| Component | Purpose |
| --------- | ------- |
| `SKILL.md` | Required metadata + concise procedural instructions; target < 500 lines, use progressive disclosure. |
| `references/domain-rules.md` | Authoritative domain rules, interpretations, taxonomies, and versioned jurisdiction overlays. |
| `references/source-map.md` | Approved systems and documents, source hierarchy, freshness requirements, and citation rules. |
| `references/controls.md` | Risk tier, prohibited actions, human approvals, case states, segregation of duties, retention, escalation paths. |
| `references/handoffs.md` | Adjacent-skill boundaries, routing criteria, required handoff artifacts, and prohibited duplicate execution. |
| `assets/output-template.*` | Approved report, memo, spreadsheet, case, register, communication, or checklist template. |
| `scripts/validate_input.*` | Deterministic checks for required fields, formats, completeness, identity, freshness, and unsafe inputs. |
| `scripts/calculate_or_transform.*` | Deterministic parsing, spreading, calculation, reconciliation, clause comparison, redaction, or transformation. |
| `scripts/validate_output.*` | Schema, tie-out, citation, rule, threshold, stale-language, prohibited-content, and handoff checks. |
| `evals/evals.json` | Representative task, trigger, routing, regression, safety, and authorization evaluations with assertions. |
| `evals/files/` | De-identified normal, edge, failure, stale-source, cross-skill, and adversarial fixtures plus golden outputs. |
| `CHANGELOG.md` | Version, scope, trigger, control, tool, data, behavior, handoff, and evaluation changes with approvals. |

Not every skill needs every component. R1/R2 read-only skills may omit
`calculate_or_transform` when there is nothing deterministic to compute; casework and
orchestration skills always carry `controls.md` and `handoffs.md`.

## Release gates (acceptance criteria)

| Gate | Criteria |
| ---- | -------- |
| **Specification** | Name and directory match; frontmatter validates; description states what and when; references are one level deep. |
| **Scope and routing** | One coherent task, explicit non-goals, positive/negative triggers, no duplicate territory, tested handoffs to adjacent skills. |
| **Sources** | Approved source hierarchy, data lineage, freshness/effective dates, citations, and jurisdiction/version labels implemented. |
| **Tools** | Least-privilege operations, deterministic schemas, bounded responses, timeout handling, durable case/job IDs, no hidden retries, audit logging. |
| **Safety and compliance** | PII controls, prohibited decisions, human approval gates, records/retention, fairness, conflicts, customer communications, and no-autonomous-closure tests pass. |
| **Quality** | Required calculations and reconciliations tie, outputs match templates, uncertainties surfaced, stale content flagged, unsupported assertions fail closed. |
| **Evaluations** | Trigger/routing precision-recall, task uplift, regression, edge, stale-source, adversarial, security, authorization, latency, and cost thresholds pass. |
| **Human acceptance** | Domain SME, control owner, legal/compliance (where applicable), accessibility, model risk (where applicable), and product owner approvals recorded. |
| **Operations** | Owner, SLOs, telemetry, incident process, rollback, versioning, recertification date, dependency/tool contract, and retirement criteria set. |
