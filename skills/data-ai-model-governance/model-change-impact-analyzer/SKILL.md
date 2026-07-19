---
name: model-change-impact-analyzer
description: >-
  Assess a proposed change to a deployed model or agent and produce an evidence-backed
  impact assessment: which dimensions change (scope, data, tools, behavior, controls,
  testing, users, regulatory surface), the resulting impact band, and a recommended
  revalidation scope and governance path. Use when a model owner, validator, or
  change-governance reviewer asks "what is the impact of this model change", "does this
  change need revalidation", "what breaks if we swap this data source / add this tool /
  loosen this threshold", or needs a review-ready change-impact pack before a governance
  decision. This skill produces findings, cited evidence, and a revalidation RECOMMENDATION
  for mandatory human adjudication only; it NEVER approves, deploys, releases, closes,
  waives revalidation for, or attests a model change, and never makes an autonomous
  regulated decision — those are human / authorized-system actions.
license: MIT
compatibility: Amazon Quick Desktop; requires model-registry, data-catalog, evaluation-harness, agent/tool-log, policy/controls, and risk/issue-tracking MCP integrations (all read-only).
metadata:
  aws-fsi-category: "Data, AI & Model Governance"
  aws-fsi-skill-type: "Analysis and evaluation skills"
  aws-fsi-risk-tier: "R3"
  aws-fsi-archetype: "Analyze & review"
  aws-fsi-agent-pattern: "Interactive decision-support copilot"
  aws-fsi-delivery-wave: "Wave 3 - regulated casework"
  aws-fsi-action-mode: "Read-only analysis"
  aws-fsi-scheduled-agent: "no"
  aws-fsi-baseline-status: "new"
  aws-fsi-human-approval: "required"
  aws-fsi-data-classification: "Confidential"
  aws-fsi-jurisdictions: "US (default); configure additional jurisdiction packs per deployment"
  aws-fsi-owner: "AI / Model Risk Governance"
  aws-fsi-primary-user: "Model owner / change governance / validator"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-07-17"
---

# Model Change Impact Analyzer

## Purpose and outcome
Given a proposed change to a governed model or agent, evaluate each **change dimension**
(scope, data, tools, behavior, controls, testing, users, regulatory surface), attach cited
evidence to every material change, map the fired set to a deterministic **impact band**, and
derive a **recommended revalidation scope and governance path**. A successful output lets a
model owner, independent validator, or change-governance forum see exactly what changed, how
material it is, and what revalidation the change would require — so a **human adjudicates**
the change. The decision to approve, deploy, waive revalidation, or close the change remains
human and is out of scope for this skill.

## Use when
- "What is the impact of this model/agent change?"
- "Does this change need revalidation, and how much?"
- "What breaks if we swap this data source / add this tool / loosen this threshold / change
  this prompt or guardrail?"
- A change-governance reviewer needs a consistent, cited change-impact pack to attach to a
  change record before adjudication.

## Do not use
- The user wants the change **approved, deployed, released, waived, closed, or attested** →
  out of scope. Produce the impact pack and route to the human adjudicator / authorized
  change-governance system. This skill never clears a change.
- The change is actually a **net-new AI use case** (not a change to an existing model) →
  `ai-use-case-intake-classifier`.
- The trigger is a **new law/regulation or supervisory guidance** (obligation mapping),
  rather than a model change → `regulatory-change-impact-analyzer`.
- The user needs the **independent revalidation performed** (conceptual soundness, testing,
  outcomes) → `model-validation-assistant`.
- The user needs a fresh **AI risk assessment** or documentation pack, not a change delta →
  `ai-risk-assessment-builder` / `model-risk-documenter`.
- For an **agent** change, deep prompt/tool/guardrail review or permission-scope review →
  `prompt-and-agent-risk-reviewer` / `agent-permission-scope-reviewer`.

## Adjacent-skill handoffs
See [references/handoffs.md](references/handoffs.md). This skill emits an impact pack with a
durable `assessment_id`; downstream validation, documentation, and inventory skills consume
it. It must not duplicate their revalidation, documentation, or record-update steps, and it
must not reach the adjudication those forums own.

## Inputs and prerequisites
- The **model/agent identity** (registry id) and its **materiality** and regulated-use flag.
- A **change record** describing each dimension with `before`/`after`, typed `risk_flags`,
  and an `evidence_ref` for every changed dimension. Schema:
  [scripts/validate_input.py](scripts/validate_input.py).
- Read access to model registry, data catalog, evaluation harness, agent/tool logs, and the
  policy/controls library; the versioned banding config (see
  [references/domain-rules.md](references/domain-rules.md)).

## Source hierarchy
See [references/source-map.md](references/source-map.md). The model registry is the record
of the model's current approved state; the change record is the proposed delta; the
policy/controls library and evaluation harness supply the control and testing baselines.
Cite every fired dimension's evidence to a source ref. Never substitute a requester's
assertion for the registry/policy record.

## Workflow
1. **Scope & identity** — confirm the model/agent, its materiality and regulated-use flag,
   and the change record; validate with `validate_input`. Fail closed on unknown identity.
2. **Evaluate dimensions (deterministic)** — run
   [scripts/calculate_or_transform.py](scripts/calculate_or_transform.py) to evaluate each
   of the eight dimensions, attach evidence + citation to every fired dimension, and record
   any dimension not supplied as `not_evaluable`. Findings are **explainable**, not a
   black-box score.
3. **Band the impact** — map the fired dimensions + critical flags + model materiality to
   an impact band (Low / Moderate / High / Critical) per the deterministic, documented
   mapping. This is a **finding**, not a decision.
4. **Derive recommendations** — from the band, state the recommended revalidation scope and
   governance path (both recommendations for a human adjudicator).
5. **Write the pack** — plain-language finding per dimension + evidence + impact band +
   recommended revalidation/governance + explicit items the adjudicator must weigh and any
   not-evaluable dimensions.

## Validation loop
Run `validate_input` before and [scripts/validate_output.py](scripts/validate_output.py)
after. The output check confirms: every fired dimension has cited evidence, the impact band
ties out to the deterministic mapping (recomputed with the same versioned banding config the
engine used, carried on `pack.config` — not hard-coded thresholds), the recommended scope
matches the band, **no
approval/deployment/closure/waiver/attestation language is present** (R3 prohibited-decision
screen), the standing disclaimer is present, and adjudicator prompts are included when any
dimension fired. Fail closed on any miss.

## Human approval
`required` (R3): mandatory human adjudication. A model owner, independent validator, and/or
change-governance forum must review the pack and decide before any revalidation is waived,
the change is approved, or the change is deployed. This skill provides evidence and a
recommendation only; it never adjudicates, deploys, or writes a system of record.

## Failure handling
- **Unknown/ambiguous model identity** → stop and confirm; never assess the wrong model.
- **Missing evidence_ref on a changed dimension** → hard error (evidence is mandatory);
  do not emit a finding without a citation.
- **Dimension not supplied** → report as `not_evaluable`; never infer a change that was not
  declared, and never assume "no change" silently for a dimension the requester omitted —
  surface the gap.
- **Stale/conflicting sources** (registry vs. change record) → cite both; do not resolve
  silently; flag for the adjudicator.
- **Thin before/after detail** → warn that the finding is low-evidence; do not overstate.
- **Tool timeout** → return the dimensions evaluated so far with a clear "incomplete" flag;
  do not band on a partial set as if complete.

## Output contract
1. **Summary** — model (id), change id, materiality, count of fired dimensions, impact band.
2. **Findings** — per fired dimension: name, plain-language reason, risk flags, before/after
   evidence (cited), and whether it carries a critical flag.
3. **Recommendations** — recommended revalidation scope and governance path (for the human
   adjudicator), explicitly not a decision.
4. **For the adjudicator** — items to weigh (in-scope vs. new use case, validation coverage,
   fair-lending/adverse-action impact, data-lineage review, monitoring/rollback).
5. **Not-evaluable dimensions / data gaps.**
6. **Machine-readable** — dimensions + evidence + band + `assessment_id` for downstream
   skills.
7. **Standing disclaimer** — "Impact assessment and revalidation recommendation only; not a
   change approval or deployment authorization. No model change has been approved, deployed,
   or attested."
See [references/controls.md](references/controls.md).

## Privacy and records
Confidential governance data. Use de-identified/reference model attributes; do not embed
customer NPI/PII or proprietary model internals beyond what evidences a fired dimension.
Retain the assessment + citations + config version per records policy; log the read and any
adjudication that consumes the pack. Never exfiltrate model or governance data.

## Gotchas
- **A finding is not a decision.** A Critical band justifies *recommended full revalidation*,
  never an approval, a waiver, or a deployment.
- **"No change declared" is not "no impact".** A dimension omitted from the change record is
  `not_evaluable`, not safe — force the requester to declare each dimension.
- **Threshold/cutoff loosening is a control change**, not a behavior tweak — it carries a
  critical flag because it moves the auto-decision surface and often the regulatory surface
  (e.g., adverse-action mapping under ECOA/Reg B).
- **Agent changes hide in "tools" and "controls"** — a new tool, broadened permission, or
  removed guardrail is a material change even when the underlying model is unchanged; route
  deep review to the agent-focused skills.
- **Do not tune banding to the change you want** — thresholds come from the versioned config,
  not from a judgment that this particular change "should" be low-impact.
- **Scope creep vs. change** — if the "change" expands the model to a new population or new
  decision, that may be a new use case (intake), not a change; flag it for the adjudicator.
