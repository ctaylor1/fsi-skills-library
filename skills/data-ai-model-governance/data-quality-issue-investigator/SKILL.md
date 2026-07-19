---
name: data-quality-issue-investigator
description: >-
  Investigate a detected data-quality issue as a durable case: profile the defect, quantify
  its impact (failure rate, affected records), trace which reports, models, and regulated
  decisions consume the data, build a timestamped chronology, resolve the owning parties, and
  assemble a cited evidence bundle with a recommended severity and remediation path. Use when
  a data steward or data-quality analyst needs to work a data-quality issue queue, understand
  the blast radius of a failing DQ rule or anomaly, or package evidence for a remediation or
  incident hand-off. HARD BOUNDARY: this skill produces evidence and RECOMMENDATIONS only. It
  NEVER closes or resolves a data-quality issue, confirms a root cause, marks data remediated,
  waives an exception, or writes a system of record — every disposition is a recommendation
  for a human owner, and material or regulated impact escalates to incident investigation.
license: MIT
compatibility: Amazon Quick Desktop; requires data-catalog, data-quality/profiling, model-registry, evaluation-harness, agent/tool-log, and risk/issue-management MCP integrations (all read-only).
metadata:
  aws-fsi-category: "Data, AI & Model Governance"
  aws-fsi-skill-type: "Analysis and evaluation skills"
  aws-fsi-risk-tier: "R3"
  aws-fsi-archetype: "Investigate & casework"
  aws-fsi-agent-pattern: "Case agent + evidence bundle"
  aws-fsi-delivery-wave: "Wave 3 - regulated casework"
  aws-fsi-action-mode: "Read-only analysis"
  aws-fsi-scheduled-agent: "no"
  aws-fsi-baseline-status: "new"
  aws-fsi-human-approval: "required"
  aws-fsi-data-classification: "Confidential"
  aws-fsi-jurisdictions: "US (default); configure additional jurisdiction packs per deployment"
  aws-fsi-owner: "AI / Model Risk Governance"
  aws-fsi-primary-user: "Data steward / data-quality analyst"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-07-17"
---

# Data-Quality Issue Investigator

## Purpose and outcome
Take a detected data-quality issue — a failing DQ rule, a profiling anomaly, or a reported
defect — and turn it into an **audit-ready case**: quantify the defect, map its downstream
blast radius, reconstruct when it occurred and was consumed, identify the accountable
parties, and recommend a severity and a remediation path. The outcome is a durable `case_id`
plus a cited evidence bundle a data owner, remediation team, or incident responder can act
on. The substantive decision — whether to remediate, how, and when to close — stays with the
human owner. This skill investigates and recommends; it never disposes.

## Use when
- "Investigate this data-quality issue / work my DQ issue queue."
- "How bad is this failing completeness rule — what does it affect?"
- "Which reports, models, and decisions consume this defective field?"
- "Assemble the evidence bundle and chronology for this data defect."
- "Is this defect the same as an issue we already have open?"

## Do not use
- **Documenting end-to-end lineage** or tracing the upstream transformation chain →
  `data-lineage-documenter`.
- **A harmful/incorrect model or agent outcome** driven by the defect (bias, privacy,
  security, resilience event) → `ai-incident-investigator`.
- **Assessing a model/pipeline change** as the suspected cause and its revalidation impact →
  `model-change-impact-analyzer`.
- **Updating the model/agent inventory record** for an affected model → `model-inventory-maintainer`.
- Any request to **close/resolve the issue, confirm the root cause, waive it, or mark the
  data remediated** → refuse; recommend and hand off to the human owner.

## Adjacent-skill handoffs
See [references/handoffs.md](references/handoffs.md). Detection/monitoring (which populates
the issue queue) is upstream and separate from this investigation; substantive remediation
and closure are downstream and human-owned. This skill emits a durable `case_id` + evidence
bundle and must not perform the lineage documenter's, incident investigator's, or remediation
owner's work.

## Inputs and prerequisites
- The issue(s) with `issue_id`, `dataset_id`, `field`, `rule_id`, `defect_type`, `period`,
  `total_records` + `failing_records`, `data_classification`, the downstream `consumers`
  (regulatory reports, internal reports, models with materiality, regulated decisions),
  `prior_issues_90d`, `owners`, timestamped `events`, and `record_keys`; plus `open_cases`
  for duplicate detection. Schema: [scripts/validate_input.py](scripts/validate_input.py).
- Read access to the data catalog, DQ/profiling results, model registry, and issue system.
- Freshness: issue state must be read fresh so a defect already under an open case is linked,
  not re-opened.

## Source hierarchy
See [references/source-map.md](references/source-map.md). The issue/case system is the system
of record for issue state and the durable `case_id`; the data catalog resolves datasets,
fields, owners, and consumers; DQ/profiling supplies the failing counts; the model registry
resolves affected models and materiality. Cite every evidence item; the severity config is a
**versioned contract**.

## Workflow
1. **Validate & normalize** — run `validate_input`; confirm each issue has the counts,
   defect type, and consumers needed to profile impact. What is missing becomes `needs-data`.
2. **Deduplicate** — match against `open_cases` on dataset + rule + period with overlapping
   record keys; link as `possible-duplicate` for human confirmation. Never auto-merge or
   auto-close.
3. **Quantify & score (deterministic)** — run
   [scripts/calculate_or_transform.py](scripts/calculate_or_transform.py): computes failure
   rate, counts affected reports/models/decisions, and derives a documented severity band
   from explainable inputs (see [references/domain-rules.md](references/domain-rules.md)).
4. **Build chronology & resolve parties** — order the timestamped events (loaded, rule run,
   first observed, last consumed) into a cited chronology; resolve data owner, steward, and
   upstream owner.
5. **Assemble evidence bundle** — durable `case_id`, defect profile, amounts, consumers,
   chronology, parties, and citations for every item; attach a recommended severity.
6. **Recommend a disposition (only)** — `recommend-incident-escalation` (material/regulated
   impact, route to incident investigation), `recommend-upstream-trace` (route to lineage),
   or `recommend-remediation` (route to the data owner). Never a closure/determination.

## Validation loop
Run `validate_input` before and [scripts/validate_output.py](scripts/validate_output.py)
after. The output check enforces: durable `case_id` on every record; only recommendation
dispositions (no closure/determination/remediation states); every evidence item and
chronology event cited; severity band ties to the deterministic mapping using the same
thresholds the engine used (the output's versioned `severity_config`, defaults otherwise);
possible-duplicates carry a linked case; and a closure/determination/filing language screen.
Fail closed on any miss.

## Human approval
`required`. Every substantive step — confirming a root cause, deciding to remediate, waiving
a defect, closing the issue, or writing any system of record — belongs to the human owner or
incident process. This skill proposes a severity and a remediation path and packages the
evidence; humans adjudicate and act.

## Failure handling
- **Unquantifiable defect** (missing counts or defect type) → `needs-data`; list exactly what
  is missing. Do not guess a failure rate or severity.
- **Ambiguous duplicate** → link as `possible-duplicate` for human confirmation; never
  auto-merge or auto-close.
- **Material / regulated consumer** (regulatory report, material model, regulated decision) →
  force `recommend-incident-escalation` and route; do not down-rank.
- **Stale/conflicting sources** → cite both and recommend escalation rather than picking one.
- **Tool timeout** → return the partial investigation with an explicit incomplete flag; no
  retry assumption.

## Output contract
1. **Issue view** — per issue: `case_id`, severity band, disposition
   (`recommend-incident-escalation` | `recommend-upstream-trace` | `recommend-remediation` |
   `needs-data` | `possible-duplicate`), one-line cited reason.
2. **Evidence bundle** (per recommended issue) — defect profile, amounts (failing records,
   failure rate, affected report/model/decision counts, monetary exposure), consumers,
   chronology, parties, citations, recommended severity.
3. **Duplicate links** — `possible-duplicate` items with their linked parent `case_id`.
4. **Data gaps / needs-data list.**
5. **Machine-readable** — the investigation records + bundles keyed by `case_id`.
6. **Standing note** — "Investigation evidence and recommendations only; no data-quality
   issue has been closed, no root cause confirmed, and no data remediated, waived, or signed
   off."
See [references/controls.md](references/controls.md).

## Privacy and records
**Confidential.** Data-quality metadata can reference datasets and fields that hold customer
NPI/PII; work from profiling counts and keys, not raw record contents, and mask any
identifier surfaced in output to what evidences the defect. Retain the investigation records,
evidence bundles, citations, and severity-config version per governance recordkeeping. Log
every read and every recommendation with the analyst identity; the case remains open until a
human owner acts.

## Gotchas
- **Recommendation ≠ resolution.** A `recommend-remediation` disposition packages evidence for
  the owner; it does not fix the data, confirm the cause, or close the issue.
- **Dedup links, never deletes.** A possible duplicate points to its parent case; the parent
  is still worked by a human.
- **Blast radius drives severity.** A small failure rate that feeds a regulatory report or a
  material model is Critical — consumers, not row counts alone, set the band.
- **Upstream cause is a hypothesis.** `upstream_suspected` routes to lineage tracing; it is
  never a confirmed root cause.
- **Severity config is versioned.** Record the config version on every case so the severity is
  reproducible and reviewable.
