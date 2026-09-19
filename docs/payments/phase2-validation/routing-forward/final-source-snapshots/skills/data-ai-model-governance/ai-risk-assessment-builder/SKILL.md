---
name: ai-risk-assessment-builder
description: >-
  Draft an AI/ML risk assessment scoring risk across ten domains (data, model, fairness,
  explainability, security, privacy, third parties, human oversight, resilience, monitoring),
  mapping each finding to cited evidence, computing a deterministic residual rating from a
  documented likelihood x impact matrix and control coverage, and packaging remediation
  findings and a pending approval-routing block from an approved template. Use when an AI
  risk, model risk, or compliance reviewer needs to build, refresh, or complete an AI/model
  risk assessment or responsible-AI review for a model, GenAI, or agentic use case, map
  controls to risk domains, or compute inherent vs residual risk (control gaps) for
  adjudication. This skill NEVER approves, certifies, or authorizes a system for deployment,
  makes no final risk determination, closes no findings, and invents no control or evidence —
  it drafts a decision-support pack a human must review and adjudicate.
license: MIT
compatibility: Amazon Quick Desktop; requires model-registry, data-catalog, evaluation-harness, agent/tool-log, policy/controlled-template, and risk/issue-management MCP integrations (all read-only; drafting only, no system-of-record change).
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
  aws-fsi-primary-user: "AI risk / model risk / compliance"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-07-17"
---

# AI Risk Assessment Builder

## Purpose and outcome
Turn a use-case intake and its declared controls into an **audit-ready AI risk assessment
draft**: score inherent and residual risk across the ten required domains (data, model,
fairness, explainability, security, privacy, third parties, human oversight, resilience,
monitoring), map every risk statement to a cited source, compute a deterministic residual
rating from a documented likelihood x impact matrix and control coverage, surface open
findings with recommended remediation, and route the pack to the correct approver — set to
`pending`. The outcome is a review-ready decision-support pack (or an itemized reason it
cannot be completed yet) that the accountable risk owner and approver **adjudicate**. The
skill never approves, certifies, closes a finding, or authorizes deployment.

## Use when
- "Build / draft an AI risk assessment (or model risk assessment) for this system."
- "Score inherent vs residual risk across the risk domains and map the controls."
- "What are the control gaps and open findings for this GenAI / agentic use case?"
- "Assemble a responsible-AI review pack for adjudication / the model risk committee."

## Do not use
- **Classifying / intaking** a use case or assigning its inherent tier → `ai-use-case-intake-classifier`.
- **Independent model validation** (performance, benchmarking, challenger testing) → `model-validation-assistant`, `ai-evaluation-benchmark-builder`.
- **Prompt / agent behavioral risk review** or **agent permission scoping** → `prompt-and-agent-risk-reviewer`, `agent-permission-scope-reviewer`.
- **Third-party AI vendor due diligence** → `third-party-ai-due-diligence-assistant`.
- **Data lineage / data-quality** deep dives → `data-lineage-documenter`, `data-quality-issue-investigator`.
- **Investigating a live AI incident** → `ai-incident-investigator`.
- Any request to **approve, certify, accept the risk, close a finding, or clear the system for production** → refuse; draft only and route to a human.

## Adjacent-skill handoffs
See [references/handoffs.md](references/handoffs.md). This skill consumes the inherent tier
and use-case metadata from `ai-use-case-intake-classifier`, control/evaluation evidence from
the model registry and evaluation harness, and emits an `assessment_id`-keyed draft pack with
`approval.status: pending` and `adjudication_required: true`. Validation, vendor diligence,
agent-risk review, and the approval decision itself belong to the routes above or to a human.

## Inputs and prerequisites
- The assessment intake: `assessment_id`, `system_name`, `use_case`, `inherent_risk_tier`
  (from intake), `intake_ref`, `model_ref`, `framework_version`, and a `domains` map. Each of
  the ten domains supplies a `likelihood` and `impact` (Low/Medium/High), a `source_ref`, and
  a list of `controls` (each with `control_id`, `status`
  implemented/partial/missing/not_applicable, `evidence_ref`, and `recommended_action`).
  Schema: [scripts/validate_input.py](scripts/validate_input.py).
- The **current** control framework / risk-domain taxonomy (`framework_version`).
- Read access to the model registry, data catalog, evaluation harness, agent/tool logs, the
  policy/controlled-template library, and the risk/issue system.

## Source hierarchy
See [references/source-map.md](references/source-map.md). The control framework / risk
taxonomy is authoritative for the required domains and scoring; the model registry is the
system of record for the model and its controls; the evaluation harness supplies fairness /
performance evidence; the risk/issue system holds open items. Cite every risk statement and
control. The framework and matrix are a **versioned contract** — record `framework_version`
on every pack.

## Workflow
1. **Validate & normalize** — run `validate_input`; confirm all ten domains are present and
   each carries likelihood, impact, a source ref, and its controls; flag a missing domain or
   missing likelihood/impact as `needs-data` (never guess a score).
2. **Compute deterministically** — run
   [scripts/calculate_or_transform.py](scripts/calculate_or_transform.py): per domain, the
   inherent band from the likelihood x impact matrix, control coverage, the residual band
   (controls reduce likelihood, never impact; residual is never eliminated), and per-domain
   findings; then the overall residual rating and approver routing. Rules:
   [references/domain-rules.md](references/domain-rules.md).
3. **Assemble the pack** — populate [assets/output-template.md](assets/output-template.md):
   system identity, per-domain inherent/residual with citations, the findings register with
   recommended remediation, the overall residual rating, and the approval block set to
   `pending`. No risk statement without a cited source; no finding without a remediation.
4. **Validate output** — run
   [scripts/validate_output.py](scripts/validate_output.py); fail closed on any miss
   (template fidelity, residual tie-out, unsupported assertion, approval discipline,
   prohibited autonomous-decision language, standing note).
5. **Never decide** — hand the reviewed draft to the accountable risk owner and approver for
   adjudication; the skill sets nothing to approved/accepted/closed.

## Validation loop
Run `validate_input` before and `validate_output` after. The output screen enforces: all ten
domains present; each domain cited; every declared residual band equals the deterministic
matrix result; a High-residual domain carries an open finding; every finding has a
remediation and a source ref; `approval.status == pending` with `adjudication_required`; no
approval/certification/deployment-clearance or finding-closure language; standing disclaimer
present. See [references/controls.md](references/controls.md). Correct and re-run until it
passes or the intake is flagged not-completable.

## Human approval
`required`. Every residual rating, finding, and the go/no-go decision must be reviewed and
adjudicated by the accountable risk owner and the routed approver before any decision,
acceptance, or deployment. This skill proposes and drafts; it never approves, certifies,
accepts risk, closes a finding, or authorizes deployment. Internal drafting is
reviewer-sampled per [references/controls.md](references/controls.md).

## Failure handling
- **Missing domain / likelihood / impact** → `needs-data`; list exactly what is missing;
  never score a domain by guessing.
- **Control with no evidence ref** → treat the control as unproven; it cannot raise coverage
  and its gap is surfaced as a finding; never assume an undocumented control is effective.
- **Unknown / superseded framework version** → stop; map to the current framework first; do
  not score against a stale taxonomy.
- **Conflicting evidence** (e.g., registry vs evaluation harness) → cite both; raise the
  residual and route to adjudication; do not silently pick one.
- **Tool timeout / partial intake** → return the partial pack with an explicit incomplete
  flag and the `framework_version` used; no retry assumption; never mark complete.

## Output contract
1. **Assessment summary** — `assessment_id`, `system_name`, `inherent_risk_tier`,
   `overall_residual_rating`, counts of findings by severity, `framework_version`.
2. **Per-domain scoring** — for each of the ten domains: likelihood, impact, inherent band,
   coverage tier, residual band, control list, and citations.
3. **Findings register** — each open finding: domain, severity, gap controls, recommended
   remediation, owner, source refs, `status: open`, `adjudication_required: true`.
4. **Approval block** — `status: pending`, routed `required_approvers`, `adjudication_required`.
5. **Machine-readable** — the assessment record keyed by `assessment_id` with `framework_version`.
6. **Standing note** — "Draft AI risk assessment for human review only; this skill does not
   approve, certify, or authorize any AI system for deployment, makes no final risk
   determination, closes no findings, and every residual rating and finding requires review
   and adjudication by the accountable risk owner and approver before any decision."
See [references/controls.md](references/controls.md).

## Privacy and records
**Confidential.** The assessment describes systems and controls, not customer data; include
only the evidence needed to substantiate a domain, and reference model/data assets by their
catalog IDs rather than copying sensitive datasets. Retain the draft pack, `framework_version`,
citations, and reviewer sign-off with the assessment record; log every read and every pack
produced with the reviewer identity. Route customer NPI/PII handled by the assessed system to
the owning system's controls, not into this pack.

## Gotchas
- **Drafting ≠ approving.** The pack is a draft with a `pending` approval block; a human
  adjudicates. Never emit "approved", "certified", "risk accepted", or "cleared to deploy".
- **Controls reduce likelihood, not impact.** A High-impact domain stays material even with
  strong controls; residual risk is never scored to zero from declared controls alone.
- **Undocumented control = no control.** A control without an evidence ref does not raise
  coverage; the gap is a finding. Never assume an unproven control works.
- **Every domain is required.** All ten domains must be scored and cited; a partial pack is
  `needs-data`, not a completed assessment.
- **Residual is deterministic.** The band comes from the documented matrix, not judgment;
  the reviewer can override in adjudication, but the draft states the computed value.
- **Framework is a versioned contract.** Record `framework_version` on every pack so the
  scoring basis is reproducible and reviewable.
