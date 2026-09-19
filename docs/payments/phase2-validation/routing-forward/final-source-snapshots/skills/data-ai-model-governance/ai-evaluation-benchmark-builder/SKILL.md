---
name: ai-evaluation-benchmark-builder
description: >-
  Draft a representative evaluation benchmark for an AI/ML/GenAI/agent system: design task,
  trigger, regression, safety, robustness, latency, and cost evaluations, each with a
  representative dataset, a metric, and an acceptance threshold and baseline that trace to an
  approved source (or are flagged proposed), plus per-dimension sample minimums, direction
  checks, and coverage mapped to the system's risk rating. Use when an AI-evaluation, quality,
  model-risk, or domain SME needs to build an eval benchmark, design the evaluation plan for a
  model/agent, set acceptance thresholds and baselines, or check eval coverage for governance
  review. Keywords: eval, benchmark, acceptance threshold, baseline, regression suite, safety/
  red-team eval, robustness, latency, cost, SR 11-7, AI RMF. Drafts ONLY: never runs or scores
  an eval, never invents a threshold or baseline, never makes a go/no-go, release, or compliance
  call, never certifies the model, and never self-approves - governance approves thresholds
  before use.
license: MIT
compatibility: Amazon Quick Desktop; requires model-registry, data-catalog, policy/regulatory-library, risk-appetite, evaluation-harness, and agent/tool-log MCP integrations (all read-only; the benchmark is drafted, never executed).
metadata:
  aws-fsi-category: "Data, AI & Model Governance"
  aws-fsi-skill-type: "Artifact-creation skills"
  aws-fsi-risk-tier: "R3"
  aws-fsi-archetype: "Draft & package"
  aws-fsi-agent-pattern: "Interactive production copilot"
  aws-fsi-delivery-wave: "Wave 1 - platform controls"
  aws-fsi-action-mode: "Draft-only; no system-of-record change"
  aws-fsi-scheduled-agent: "no"
  aws-fsi-baseline-status: "new"
  aws-fsi-human-approval: "required"
  aws-fsi-data-classification: "Confidential"
  aws-fsi-jurisdictions: "US (default); configure additional jurisdiction packs per deployment"
  aws-fsi-owner: "AI / Model Risk Governance"
  aws-fsi-primary-user: "AI evaluation / quality engineering / domain SME"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-07-17"
---

# AI Evaluation Benchmark Builder

## Purpose and outcome
Turn a model/agent and its approved sources into an audit-ready, source-linked **evaluation
benchmark package (DRAFT)**: a set of evaluations spanning task, trigger, regression, safety,
robustness, latency, and cost, each with a representative dataset, a metric, an acceptance
threshold and a baseline that trace to an approved source (or are explicitly flagged
`proposed`), a documented sample minimum, and a coverage matrix for the system's risk rating.
The outcome is a review-ready benchmark (or a clear, itemized list of what blocks it) that
model-risk governance approves before it is ever run. The skill never runs the evaluations,
never scores the model, and never decides release.

## Use when
- "Build / design the evaluation benchmark for model MDL-XXXX (or this agent)."
- "Set acceptance thresholds and baselines for these evaluations."
- "What evaluation coverage does this high-risk use case need?"
- "Assemble a regression + safety + latency + cost eval plan for governance review."

## Do not use
- **Running / scoring** the evaluations or producing pass/fail results → an authorized
  evaluation harness operated by engineering/MLOps under governance oversight (no catalog skill
  executes evaluations); interpreting the resulting outcomes against the approved thresholds is
  `model-validation-assistant`.
- **Classifying** the use case or setting the inherent risk tier → `ai-use-case-intake-classifier`.
- **Maintaining the inventory record** (ownership, materiality, lifecycle) → `model-inventory-maintainer`.
- **Deep red-team / adversarial** probe design → `prompt-and-agent-risk-reviewer`.
- **Fairness / disparate-impact** test design → `ai-risk-assessment-builder`.
- **Independent validation report** drafting → `model-risk-documenter`.
- Any request to **run it, decide go/no-go, certify, or approve** → refuse; draft only and route
  to governance.

## Adjacent-skill handoffs
See [references/handoffs.md](references/handoffs.md). This skill is benchmark *design* only. It
consumes the `model_id` + risk rating from intake/inventory and approved thresholds from policy/
risk-appetite, and emits a `spec_version`-keyed draft package with `governance_approval: pending`.
Execution, results analysis, validation reporting, and specialist test design belong to the
routes above or to an authorized human.

## Inputs and prerequisites
- The build request: `spec_version`, the `system_under_eval` (`model_id`, `risk_rating` in
  High/Medium/Low, plus name/version/use case/registry ref), the `approved_sources` list
  (policy, regulation, risk appetite, SLA, prior model card — each with a `source_id`), and the
  `requirements` (each: `eval_id`, `dimension`, `metric`, `dataset_ref`, `sample_size`, and an
  optional `threshold` + `baseline` with a `source_id`). Schema:
  [scripts/validate_input.py](scripts/validate_input.py).
- Read access to the model registry, data catalog, policy/risk-appetite library, evaluation
  harness (metrics only), and agent/tool logs.

## Source hierarchy
See [references/source-map.md](references/source-map.md). The model registry is authoritative
for the system and its risk rating; policy and the risk appetite statement are authoritative
for approved thresholds; the data catalog for representative datasets. Cite every threshold,
baseline, and dataset. Thresholds and baselines are a **versioned contract** — record
`spec_version` and each `source_id` on every package.

## Workflow
1. **Validate & normalize** — run `validate_input`; confirm the system, approved sources, and
   requirements are structurally complete; warn on gaps that will force `needs-data` /
   `needs-calibration` / `insufficient-sample`.
2. **Build deterministically** — run
   [scripts/calculate_or_transform.py](scripts/calculate_or_transform.py): resolve each
   threshold/baseline provenance against the approved sources, check metric direction and the
   per-dimension sample minimum, assign a status, and compute the coverage matrix for the risk
   rating. Rules: [references/domain-rules.md](references/domain-rules.md).
3. **Assign status** — per eval: `needs-data`, `direction-mismatch`, `insufficient-sample`,
   `needs-calibration`, or `ready-for-review`; package: `draft-incomplete` until coverage is
   complete and every eval is ready, then `ready-for-governance-review`.
4. **Draft the package** — assemble from [assets/output-template.md](assets/output-template.md):
   system identity, coverage, per-eval specs with provenance, open items, and the governance
   approvals block. No threshold or baseline without an approved source or a `proposed` flag.
5. **Validate output** — run
   [scripts/validate_output.py](scripts/validate_output.py); fail closed on any miss.
6. **Never run or decide** — hand the reviewed draft to model-risk governance for approval; a
   separate skill/harness executes it.

## Validation loop
Run `validate_input` before and `validate_output` after. The output screen enforces: template
fidelity + full per-eval fields; approved-only for anything `ready`; no invented/unsourced
values; coverage integrity; `governance_approval == pending` and `reviewer_signoff_required`;
no determination/certification/release language; standing note present. See
[references/controls.md](references/controls.md). Correct and re-run until it passes or the
package is flagged `draft-incomplete`.

## Human approval
`required`. Model-risk governance (MRM/MRG) must review and approve the benchmark, its
acceptance thresholds, and its baselines before it is used to evaluate, gate, or release any
model. This skill proposes and drafts; it never runs, never scores, never certifies, and never
self-approves. Authoring the thresholds and approving them are segregated duties.

## Failure handling
- **Unknown / out-of-taxonomy dimension** → `needs-data`; map it to the 7-dimension taxonomy
  first; do not invent a dimension.
- **Missing representative dataset or metric** → `needs-data`; never fabricate a dataset to
  fill coverage.
- **Threshold/baseline without an approved source** → `needs-calibration` and `proposed`;
  never promote an unsourced number to `approved`.
- **Sample below the documented minimum** → `insufficient-sample`; surface the gap.
- **Operator contradicts metric direction** → `direction-mismatch`; do not silently reinterpret.
- **Tool timeout / stale sources** → return partial output with an explicit incomplete flag and
  the `spec_version` used; no retry assumption.

## Output contract
1. **Benchmark queue / summary** — per eval: `eval_id`, `dimension`, `metric` + direction,
   dataset, acceptance rule with provenance, baseline with provenance, sample vs minimum, and
   `status`; plus status counts.
2. **Coverage matrix** — required vs present dimensions for the risk rating and `complete`.
3. **Benchmark package** (draft) — following [assets/output-template.md](assets/output-template.md),
   with the approvals block (`governance_approval: pending`, `reviewer_signoff_required: true`).
4. **Open items** — every `proposed` / `needs-data` / `insufficient-sample` / `direction-mismatch`
   evaluation with what it needs.
5. **Machine-readable** — the benchmark records keyed by `eval_id` with `spec_version`.
6. **Standing note** — "Draft evaluation benchmark for human review only; this skill does not
   run the evaluations, does not score or certify the model, and makes no go/no-go, release, or
   compliance determination — every threshold and baseline must be approved by model risk
   governance before use."

## Privacy and records
**Confidential.** Evaluation datasets may carry customer or proprietary content; reference them
by catalog id and lineage rather than embedding records (data minimization). Retain the drafted
benchmark, `spec_version`, source citations, and reviewer sign-off with the model record per
model-risk recordkeeping; log every read and every package produced with the author identity.

## Gotchas
- **Designing ≠ running.** The package is a plan; a separate harness/skill runs it and a human
  approves it. Never emit results, "passed/failed", or release language.
- **Never invent a number.** An acceptance threshold or baseline with no approved source is
  `proposed`, not `approved`, and keeps the eval `needs-calibration`.
- **Coverage is risk-scaled.** A high-risk system needs all seven dimensions; a thin plan that
  skips safety or regression is `draft-incomplete`, not ready.
- **Direction matters.** A `lower-is-better` metric with a `>=` threshold is a
  `direction-mismatch`, not a passing spec.
- **Sample minimums are documented, not optional.** Safety needs far more samples than latency;
  below the minimum is `insufficient-sample`.
- **Thresholds are a versioned contract.** Record `spec_version` and each `source_id` so the
  acceptance basis is reproducible and reviewable, and so governance approves a fixed artifact.
