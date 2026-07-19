---
name: model-validation-assistant
description: >-
  Support independent model validation: assess conceptual soundness, data, performance,
  outcomes, limitations, controls, and monitoring; credit only independently evidenced results
  (developer-attested claims earn no credit); generate open, cited validation findings with a
  deterministic severity; and package a validation-findings draft with a recommended disposition
  and a pending approver-routing block from an approved template. Use when a model validator or
  quantitative-risk reviewer needs to perform, refresh, or complete an independent validation of
  a model, GenAI, or agentic system under SR 11-7 / model-risk standards, test conceptual and
  empirical soundness, analyze data and outcomes, or assess limitation and control coverage. This
  skill NEVER approves, certifies, or clears a model for use, makes no final validation decision,
  closes no finding, and assembles no governed documentation pack (kept separately by
  model-risk-documenter) - it drafts decision-support findings a human must review and adjudicate.
license: MIT
compatibility: Amazon Quick Desktop; requires model-registry/inventory, data-catalog, evaluation-harness, agent/tool-log, policy/controlled-template, and risk/issue-management MCP integrations (all read-only; drafting only, no system-of-record change).
metadata:
  aws-fsi-category: "Data, AI & Model Governance"
  aws-fsi-skill-type: "Artifact-creation skills"
  aws-fsi-risk-tier: "R3"
  aws-fsi-archetype: "Draft & package"
  aws-fsi-agent-pattern: "Interactive production copilot"
  aws-fsi-delivery-wave: "Wave 3 - regulated casework"
  aws-fsi-action-mode: "Draft-only; no system-of-record change"
  aws-fsi-scheduled-agent: "no"
  aws-fsi-baseline-status: "new"
  aws-fsi-human-approval: "required"
  aws-fsi-data-classification: "Confidential"
  aws-fsi-jurisdictions: "US (default); configure additional jurisdiction packs per deployment"
  aws-fsi-owner: "AI / Model Risk Governance"
  aws-fsi-primary-user: "Model validator / quantitative risk"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-07-17"
---

# Model Validation Assistant

## Purpose and outcome
Turn a model's developer evidence and the validator's independent testing into an **audit-ready
independent validation-findings draft**: assess the seven required areas (conceptual soundness,
data, performance, outcomes analysis, limitations, controls, ongoing monitoring), credit a `pass`
**only** where the validator holds independent evidence, generate open findings with a
deterministic severity and cited remediation, roll up an overall severity, and route the pack to
the correct approver — set to `pending`. The outcome is a review-ready, traceable
decision-support pack (or an itemized reason it cannot be completed yet) that the model
validation lead and approver **adjudicate**. The governed model documentation pack (validation
report of record) is maintained separately by `model-risk-documenter`; this skill produces the
findings, never the decision and never the documentation of record.

## Use when
- "Perform / draft an independent validation for this model (or GenAI / agentic system)."
- "Test conceptual soundness and empirical performance; analyze the data and the outcomes."
- "What are the validation findings and control/limitation coverage gaps for this model?"
- "Assemble a validation-findings pack for adjudication / the model risk committee."

## Do not use
- **Maintaining the model inventory / registry record** → `model-inventory-maintainer`.
- **Assembling / finalizing the governed model documentation pack** (validation report of record)
  → `model-risk-documenter`.
- **Building the AI/model risk assessment** (likelihood x impact, control coverage) →
  `ai-risk-assessment-builder`.
- **Building or refreshing an evaluation benchmark suite** → `ai-evaluation-benchmark-builder`.
- **Analyzing the impact of a proposed model change / re-validation trigger** →
  `model-change-impact-analyzer`.
- **Data-quality investigation / data lineage** → `data-quality-issue-investigator`,
  `data-lineage-documenter`.
- **Investigating a live model/AI incident** → `ai-incident-investigator`.
- Any request to **approve, certify, clear the model for use, accept the risk, close a finding, or
  file/assemble the documentation of record** → refuse; draft only and route to a human.

## Adjacent-skill handoffs
See [references/handoffs.md](references/handoffs.md). This skill consumes the model of record and
tier from `model-inventory-maintainer` / the registry, independent evidence from
`ai-evaluation-benchmark-builder` / the evaluation harness, and the required areas and routing
from the model risk framework; it emits a `validation_id`-keyed draft with
`validation_outcome.status: pending` and `adjudication_required: true`. Documentation assembly,
the risk assessment, change-impact analysis, and the validation decision itself belong to the
routes above or to a human.

## Inputs and prerequisites
- The validation intake: `validation_id`, `model_id`, `model_name`, `model_tier`,
  `validation_type`, `intake_ref`, `framework_version`, and an `areas` map. Each of the seven
  areas supplies a `status` (pass/deficiency/not_tested), a `materiality` (Low/Medium/High), an
  `independent_evidence` flag, a `source_ref`, an optional list of `tests` (each with `test_id`,
  `outcome` pass/fail/inconclusive, `evidence_ref`), and a `recommended_action`. Schema:
  [scripts/validate_input.py](scripts/validate_input.py).
- The **current** model risk framework / validation standard (`framework_version`).
- Read access to the model registry/inventory, data catalog, evaluation harness, agent/tool logs,
  the policy/controlled-template library, and the risk/issue system.

## Source hierarchy
See [references/source-map.md](references/source-map.md). The model risk framework / validation
standard is authoritative for the required areas, severity mapping, and approver routing; the
model registry is the system of record for the model and its declared controls; the evaluation
harness supplies independent performance/benchmark/outcome evidence; the risk/issue system holds
open items. Independent evidence outranks developer-attested claims. Cite every validation
statement and finding. The framework and template are a **versioned contract** — record
`framework_version` on every pack.

## Workflow
1. **Validate & normalize** — run `validate_input`; confirm all seven areas are present and each
   carries a status, materiality, an independence flag, a source ref, and any tests; flag a
   missing area or missing status/materiality as `needs-data` (never guess a status).
2. **Derive independently (deterministic)** — run
   [scripts/calculate_or_transform.py](scripts/calculate_or_transform.py): per area, compute the
   effective validated status (a `pass` counts only with independent evidence and no failing/
   inconclusive test; a failed test forces `deficiency`; anything else is `not_tested`), generate
   an open finding for every `deficiency`/`not_tested` area with a severity equal to the area's
   materiality, roll up the overall severity (highest-wins), and route the approver with the
   outcome set to `pending`. Rules: [references/domain-rules.md](references/domain-rules.md).
3. **Assemble the pack** — populate [assets/output-template.md](assets/output-template.md): model
   identity, per-area declared vs. independently validated status with citations, the findings
   register with recommended remediation, the overall severity and recommended disposition, and
   the validation-outcome block set to `pending`. No validation statement without a cited source;
   no credited `pass` without independent evidence; no finding without a remediation.
4. **Validate output** — run [scripts/validate_output.py](scripts/validate_output.py); fail closed
   on any miss (template fidelity, source mapping, deterministic tie-out, approval discipline,
   prohibited autonomous-decision/filing/documentation-assembly language, standing note).
5. **Never decide** — hand the reviewed draft to the model validation lead and approver for
   adjudication; the skill sets nothing to approved/accepted/cleared/closed and assembles no
   documentation of record.

## Validation loop
Run `validate_input` before and `validate_output` after. The output screen enforces: all seven
areas present; each area cited; every credited `pass` independently evidenced; each declared
`validated_status` equal to the deterministic recompute; every `deficiency`/`not_tested` area
carrying an open finding; `overall_finding_severity` equal to the highest finding severity;
`validation_outcome.status == pending` with `adjudication_required` and consistent routing; no
approval/certification/clearance, finding-closure, filing, or documentation-assembly language;
standing disclaimer present. See [references/controls.md](references/controls.md). Correct and
re-run until it passes or the intake is flagged not-completable.

## Human approval
`required`. Every finding, the overall severity, and the recommended disposition must be reviewed
and adjudicated by the model validation lead and the routed approver (Head of Model Validation, or
Model Risk Committee + CRO for High severity) before any validation decision. This skill proposes
and drafts; it never approves, certifies, clears a model, accepts risk, closes a finding, or
assembles the documentation of record. Internal drafting is reviewer-sampled per
[references/controls.md](references/controls.md).

## Failure handling
- **Missing area / status / materiality** → `needs-data`; list exactly what is missing; never
  score an area by guessing.
- **Developer-attested `pass` with no independent evidence** → downgrade to `not_tested`; surface
  a coverage/independence gap; never accept an unverified pass.
- **Failed test contradicting a declared `pass`** → force `deficiency`; the independent evidence
  governs.
- **Unknown / superseded framework version** → stop; map to the current framework first; do not
  validate against a stale standard.
- **Conflicting evidence** (registry vs. evaluation harness) → cite both; raise the finding and
  route to adjudication; do not silently pick one.
- **Tool timeout / partial intake** → return the partial pack with an explicit incomplete flag and
  the `framework_version` used; no retry assumption; never mark complete.

## Output contract
1. **Validation summary** — `validation_id`, `model_id`, `model_name`, `model_tier`,
   `overall_finding_severity`, `recommended_disposition`, counts of findings by severity and areas
   by status, `framework_version`.
2. **Per-area assessment** — for each of the seven areas: materiality, declared status,
   independently validated status, the `independent_evidence` flag, the derived
   `independently_sourced` flag (independent evidence + an independent source ref) the output
   screen re-checks, and citations.
3. **Findings register** — each open finding: area, type (`deficiency` | `coverage-gap`),
   severity, recommended remediation, owner, source refs, `status: open`,
   `adjudication_required: true`.
4. **Validation-outcome block** — `status: pending`, routed `required_approvers`,
   `adjudication_required`.
5. **Machine-readable** — the validation record keyed by `validation_id` with `framework_version`.
6. **Standing note** — "Draft independent model-validation findings for human review only; this
   skill does not approve, certify, or authorize any model for use, makes no final validation
   decision, closes no findings, assembles no governed model documentation pack, and every finding
   and recommended disposition requires review and adjudication by the model validation lead and
   approver before any decision."
See [references/controls.md](references/controls.md).

## Privacy and records
**Confidential.** The pack describes a model, its tests, and controls, not customer data; include
only the evidence needed to substantiate an area, and reference model/data assets by their catalog
IDs rather than copying sensitive datasets. Retain the draft pack, `framework_version`, citations,
and validator sign-off with the validation record; log every read and every pack produced with the
validator identity. Route customer NPI/PII handled by the assessed model to the owning system's
controls, not into this pack.

## Gotchas
- **Validating ≠ approving.** The pack is a draft with a `pending` outcome block; a human
  adjudicates. Never emit "approved for use", "validation passed", "cleared for production", or
  "risk accepted".
- **Independence is the control.** A `pass` attested only by the developer earns no credit and is
  a coverage/independence gap; the validator's own evidence is what counts.
- **A failed test governs.** A `fail` recorded against an area forces a deficiency even if the area
  was declared a pass — evidence over assertion.
- **Findings, not documentation.** This skill produces validation findings; the governed model
  documentation pack (validation report of record) is assembled by `model-risk-documenter`. Do not
  claim to have written, finalized, or filed it.
- **Every area is required.** All seven areas must be assessed and cited; a partial pack is
  `needs-data`, not a completed validation.
- **Severity is deterministic.** It comes from the area's materiality and the independent status,
  not judgment; the validator can override in adjudication, but the draft states the computed
  value.
- **Framework is a versioned contract.** Record `framework_version` on every pack so the basis is
  reproducible and reviewable.
