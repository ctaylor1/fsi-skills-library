---
name: model-risk-documenter
description: >-
  Assemble a controlled model / AI documentation and validation-evidence pack across the ten
  required sections (purpose, methodology, data, performance, limitations, controls, monitoring,
  changes, approvals, traceability), mapping every section to a versioned, cited source artifact,
  flagging untraceable or missing evidence as open documentation findings, recording only cited
  approvals, and routing to the correct approver from an approved template. Use when a model
  risk, validation, or model-owner user needs to build, refresh, or
  complete a model documentation set or validation-evidence pack (e.g., SR 11-7 model
  documentation), check source-to-document traceability, or assemble a pack for the model risk
  committee. This skill NEVER validates, approves, attests, certifies, or clears a model for use,
  makes no fitness-for-use or documentation-complete determination, closes no findings, and
  records no uncited approval (no false attestation) — it drafts a decision-support pack a human
  must review and adjudicate.
license: MIT
compatibility: Amazon Quick Desktop; requires model-registry, development/validation-artifact, data-catalog/lineage, monitoring/MLOps, controls/approval-memo, policy/controlled-template, and risk/issue-management MCP integrations (all read-only; drafting only, no system-of-record change).
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
  aws-fsi-primary-user: "Model risk / validation / model owner"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-07-17"
---

# Model Risk Documenter

## Purpose and outcome
Turn a model's development, validation, data, monitoring, controls, change, and approval
artifacts into an **audit-ready model documentation / validation-evidence pack**: assemble the
ten required sections (purpose, methodology, data, performance, limitations, controls,
monitoring, changes, approvals, traceability), map each section to a **versioned, cited** source
artifact, mark it `documented`, a `gap` (present but untraceable or missing required coverage),
or `needs-data` (absent), surface every gap and carried validation finding as an **open**
documentation finding, record only approvals that carry a citation, and route the pack to the
correct approver with the attestation block set to `pending`. The outcome is a review-ready
decision-support pack (or an itemized reason it is not yet complete) that the model owner,
independent validation, and the approver **adjudicate**. The skill never validates, approves,
attests, certifies, or clears the model.

## Use when
- "Assemble / build / refresh the model documentation pack for this model."
- "Put together the validation-evidence pack (SR 11-7 documentation) for the committee."
- "Which sections are missing or have untraceable evidence before validation review?"
- "Check source-to-document traceability for this model's documentation."

## Do not use
- **Independent model validation / testing** (conceptual soundness, performance, challenger) → `model-validation-assistant`.
- **Maintaining the inventory record** (identity, tier, lifecycle) → `model-inventory-maintainer`.
- **Assessing a proposed change / revalidation need** → `model-change-impact-analyzer`.
- **Building the AI/model risk assessment** (inherent vs residual scoring) → `ai-risk-assessment-builder`.
- **Data lineage / data-quality** deep dives → `data-lineage-documenter`, `data-quality-issue-investigator`.
- **Agent behavioral / permission review** → `prompt-and-agent-risk-reviewer`, `agent-permission-scope-reviewer`.
- Any request to **validate, approve, attest, certify, clear the model, or close a finding** → refuse; draft only and route to a human.

## Adjacent-skill handoffs
See [references/handoffs.md](references/handoffs.md). This skill consumes the model identity and
**tier** from `model-inventory-maintainer`, validation results and findings from
`model-validation-assistant`, lineage from `data-lineage-documenter`, and the template/framework
from the controlled-template library; it emits a `model_id`-keyed draft with
`attestation.status: pending` and `adjudication_required: true`. Validation, the inventory
record, change analysis, and the approval decision belong to the routes above or to a human.

## Inputs and prerequisites
- The documentation intake: `template_version`, `framework_version`, `model_id`, `model_name`,
  `model_tier`, `model_version`, and a `sections` map. Each of the ten sections supplies a
  `content_ref`, a list of `source_artifacts` (each with `artifact_id`, `artifact_type`,
  `version`, `date`), and a `coverage` list; plus optional `findings` (open validation findings)
  and `approvals` (each with a `reference`). Schema:
  [scripts/validate_input.py](scripts/validate_input.py).
- The **current** model-risk documentation template and required-coverage list (`template_version`).
- Read access to the model registry, development/validation artifacts, data catalog/lineage,
  monitoring evidence, controls/approval memos, the controlled-template library, and the
  risk/issue system.

## Source hierarchy
See [references/source-map.md](references/source-map.md). The documentation template / framework
is authoritative for the required sections, coverage, and routing; the model registry is the
system of record for identity and tier; validation reports supply performance/limitations
evidence and findings. Cite every section to a **versioned** artifact — an unversioned artifact
is untraceable and earns no credit. The template and framework are a **versioned contract**
(`template_version` / `framework_version`) — record both on every pack.

## Workflow
1. **Validate & normalize** — run `validate_input`; confirm all ten sections are present and
   each carries a `content_ref`, `source_artifacts`, and `coverage`; flag missing content
   (`needs-data`) or an unversioned artifact (`gap`); never guess or fabricate a version.
2. **Assemble deterministically** — run
   [scripts/calculate_or_transform.py](scripts/calculate_or_transform.py): per section, derive
   the status (`documented` / `gap` / `needs-data`) from content, versioned citation, and
   required coverage; carry open validation findings through unchanged; generate an open
   documentation finding per gap/needs-data section; record only cited approvals; roll up
   traceability, readiness, and tier-based approver routing. Rules:
   [references/domain-rules.md](references/domain-rules.md).
3. **Assemble the pack** — populate [assets/output-template.md](assets/output-template.md):
   model identity, per-section traceability with citations, the findings register (all `open`),
   the approvals-on-record table, and the attestation block set to `pending`. No section marked
   `documented` without a versioned citation; no approval recorded without a reference.
4. **Validate output** — run
   [scripts/validate_output.py](scripts/validate_output.py); fail closed on any miss (template
   fidelity, traceability tie-out, methodology/limitation coverage, finding discipline, no false
   attestation, prohibited-decision language, standing note).
5. **Never decide** — hand the reviewed draft to the model owner, independent validation, and the
   approver for adjudication; the skill sets nothing to validated/approved/attested/closed.

## Validation loop
Run `validate_input` before and `validate_output` after. The output screen enforces: all ten
sections present; each `documented` section carries a versioned citation and equals the
deterministic re-derivation; methodology and limitations carry their required coverage; every
finding is `open`, sourced, and remediated; every gap/needs-data section has an open finding;
every recorded approval is cited; `attestation.status == pending` with `adjudication_required`;
no validation/approval/attestation/certification/clearance or finding-closure language; standing
note present. See [references/controls.md](references/controls.md). Correct and re-run until it
passes or the intake is flagged not-completable.

## Human approval
`required`. Every section status, finding, recorded approval, and the documentation-complete /
model-validated determination must be reviewed and adjudicated by the model owner, independent
validation, and the routed approver before any decision, attestation, or clearance. This skill
proposes and drafts; it never validates, approves, attests, certifies, clears a model, or closes
a finding. Internal drafting is reviewer-sampled per [references/controls.md](references/controls.md).

## Failure handling
- **Missing section / content** → `needs-data`; list exactly what is missing; never draft a
  section from nothing.
- **Unversioned / undocumented artifact** → the section is a `gap`; the artifact earns no
  citation credit; the gap is surfaced as an open finding; never invent a version.
- **Unknown / superseded template version** → stop; map to the current template first; do not
  assemble against a stale required-section list or routing.
- **Approval with no cited memo** → do not record it as evidence; surface it under
  `unsupported_approvals`; never attest an approval that is not on record.
- **Conflicting evidence** (e.g., registry vs validation report) → cite both; keep the section a
  gap and route to adjudication; do not silently pick one.
- **Tool timeout / partial intake** → return the partial pack with an explicit incomplete flag
  and the `template_version` used; no retry assumption; never mark complete.

## Output contract
1. **Pack summary** — `model_id`, `model_name`, `model_tier`, `pack_status`, `readiness`,
   traceability counts, findings by severity, `template_version` / `framework_version`.
2. **Section traceability** — for each of the ten sections: status, coverage, versioned
   citations, and owner.
3. **Findings register** — each open finding: `finding_id`, section, severity, reason,
   recommended remediation, owner, source refs, `status: open`, `adjudication_required: true`.
4. **Approvals on record** — only cited approvals; uncited approvals listed as
   `unsupported_approvals` (not recorded as evidence).
5. **Attestation block** — `status: pending`, tier-routed `required_approvers`,
   `adjudication_required`.
6. **Machine-readable** — the pack record keyed by `model_id` with `template_version`.
7. **Standing note** — "Draft model documentation pack for human review only; this skill
   assembles and traces evidence but does not validate, approve, attest, or certify any model or
   AI system, makes no fitness-for-use determination, closes no findings, and every section,
   finding, and approval requires review and adjudication by the model owner, independent
   validation, and the approver before any decision."
See [references/controls.md](references/controls.md).

## Privacy and records
**Confidential.** The pack describes a model and its controls, not customer data; reference
model/data assets by catalog ID and cite evidence rather than copying sensitive datasets or
customer NPI/PII into the pack. Retain the draft pack, `template_version` / `framework_version`,
citations, and reviewer sign-off with the model record; log every read and every pack produced
with the reviewer identity, per model-risk recordkeeping.

## Gotchas
- **Documenting ≠ validating or approving.** The pack is a draft with a `pending` attestation
  block; a human validates, approves, and attests. Never emit "validated", "approved for use",
  "fit for use", "certified", or "cleared to deploy".
- **No version, no citation.** An artifact without a version is untraceable; the section becomes
  a `gap` and earns no traceability credit. Never fabricate a version to close the gap.
- **No false attestation.** Record an approval only where a cited memo exists; an uncited
  approval is flagged, never transcribed as evidence.
- **Every section is required.** All ten sections are assembled; a section with no content is
  `needs-data`, not omitted, and the pack is `needs-data` until it is supplied.
- **Findings stay open.** Carried validation findings and generated documentation gaps are all
  `open`; this skill never closes, resolves, or waives a finding.
- **Template and framework are versioned contracts.** Record `template_version` and
  `framework_version` on every pack so the basis is reproducible and reviewable.
