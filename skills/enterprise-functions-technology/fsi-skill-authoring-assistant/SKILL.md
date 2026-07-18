---
name: fsi-skill-authoring-assistant
description: >-
  Draft and validate a complete FSI Agent Skill package from an APPROVED skill spec: map the
  archetype and risk tier to the required components, assemble specification-valid frontmatter
  and the standard body sections, wire deterministic validation and eval scripts, and produce a
  review-ready authoring plan that ties every claim to the build standards and lists the
  approvals still owed. Use when a skill engineer, product owner, or developer wants to scaffold
  a new FSI skill, check a draft package for completeness and template fidelity, or confirm
  frontmatter metadata and source hierarchy. Keywords: skill authoring, SKILL.md, frontmatter,
  archetype, risk tier, package scaffold, evals. This skill NEVER publishes, registers, releases,
  signs off, or promotes a skill into the catalog, never approves its own output, never
  fabricates metadata, sources, evaluations, or approvals, and never marks a package validated or
  released without recorded human approvals - it drafts for human review and authorized release.
license: MIT
compatibility: Amazon Quick Desktop; requires controlled-template/library, knowledge & source systems, developer tooling (repo, validate_skills, run_selftests), evaluation-harness, and project-tracking/approval-record MCP integrations (all read-only; publishing/registration is out of scope).
metadata:
  aws-fsi-category: "Enterprise Functions & Technology"
  aws-fsi-skill-type: "Utility skills"
  aws-fsi-risk-tier: "R2"
  aws-fsi-archetype: "Draft & package"
  aws-fsi-agent-pattern: "Skill engineering copilot"
  aws-fsi-delivery-wave: "Wave 1 - platform controls"
  aws-fsi-action-mode: "Draft-only; no system-of-record change"
  aws-fsi-scheduled-agent: "no"
  aws-fsi-baseline-status: "new"
  aws-fsi-human-approval: "external-delivery"
  aws-fsi-data-classification: "Confidential"
  aws-fsi-jurisdictions: "US (default); configure additional jurisdiction packs per deployment"
  aws-fsi-owner: "Enterprise Functions & Technology"
  aws-fsi-primary-user: "FSI skill engineer / product owner / developer"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-07-17"
---

# FSI Skill Authoring Assistant

## Purpose and outcome
Turn an **approved** skill spec into an audit-ready **skill-package draft**: resolve the
required components from the build archetype and risk tier, assemble specification-valid
frontmatter and the standard body sections, wire the deterministic `validate_input` /
`validate_output` / eval scripts, and render a review-ready authoring plan that ties every
claim to the build standards. The outcome is a review-ready package (or a clear, itemized
reason it cannot be packaged yet) that a human reviews, approves, and releases. The skill
never publishes, never approves its own output, and never guarantees a release.

## Use when
- "Scaffold a new FSI skill for <spec> / draft the package for <skill-name>."
- "Which components and frontmatter does a Draft & package R2 skill need?"
- "Check this draft package for completeness and template fidelity before review."
- "Is the frontmatter metadata valid and consistent with the risk tier and catalog?"

## Do not use
- **Exercising a domain task** (triage an alert, reconcile a ledger, price a trade,
  adjudicate a claim) → the relevant **domain skill**; this skill authors packages, it does
  not run them.
- **Publishing / registering** a skill into the catalog or a system of record → the
  **release pipeline / catalog owner** (authorized human).
- **Approving** a package (owner, SME, control, legal, model-risk sign-off) → the **named
  human approver**; approval is never granted here.
- **Building the catalog** from the source spreadsheet → `tools/build_catalog_from_xlsx.py`
  (repo tooling, run by a maintainer).
- Any request to **publish, register, release, or self-approve** → refuse; draft only and
  route to a human.

## Adjacent-skill handoffs
See [references/handoffs.md](references/handoffs.md). This skill is authoring only. It
consumes the approved spec and `build_standard_version` from portfolio governance and the
build standards, the target entry from the catalog, and domain artifacts from the SMEs; it
emits a `skill_id`-keyed authoring plan with an approval checklist and a
`reviewer_signoff_required` posture. Release, approval, and running the authored skill belong
to the routes above or to an authorized human/pipeline.

## Inputs and prerequisites
- The build request: `skill_id`, `name`, `directory`, `category`, `archetype`, `risk_tier`,
  `action_mode`, `human_approval`, `scheduled_agent`, the proposed `metadata` (aws-fsi-*
  map), the `components_present` inventory, and any readiness `claims` (each citing an
  `approval_id`) plus recorded `approvals`. Optional: `applies_domain_rules`,
  `has_deterministic_computation`. Schema:
  [scripts/validate_input.py](scripts/validate_input.py).
- The **current** build standards, metadata schema, and catalog entry (`build_standard_version`).
- Read access to the standards/schema, catalog, domain artifacts, templates, developer
  tooling, and approval records.

## Source hierarchy
See [references/source-map.md](references/source-map.md). The build standards and metadata
schema are authoritative for required components and allowed values; the catalog is
authoritative for the target skill's name, category, and primary user; domain artifacts
supply the rules the drafted skill encodes. Cite every source. Standards, schema, and catalog
are a **versioned contract** — record `build_standard_version` on every plan.

## Workflow
1. **Validate & normalize** — run `validate_input`; confirm the spec and metadata are
   structurally complete; flag an unknown archetype or absent metadata as `needs-data`.
2. **Plan deterministically** — run
   [scripts/calculate_or_transform.py](scripts/calculate_or_transform.py): resolve required
   components (archetype + tier), diff against `components_present`, check metadata
   completeness / allowed values / tier consistency, resolve the approvals owed, and test
   each readiness claim against a recorded approval. Rules:
   [references/domain-rules.md](references/domain-rules.md).
3. **Assign status** — `needs-data`, `metadata-incomplete`, `missing-components`, or
   `unsupported-claim` blocks packaging with an itemized reason; only a clean record becomes
   `draft-package`.
4. **Draft the package** — for a packageable request, assemble the authoring plan from
   [assets/output-template.md](assets/output-template.md): identifiers, rendered frontmatter
   block, component checklist, source-map plan, approval checklist, and the reviewer
   sign-off block. No claim without a recorded approval.
5. **Validate output** — run
   [scripts/validate_output.py](scripts/validate_output.py); fail closed on any miss.
6. **Never publish** — hand the reviewed draft to an authorized human/pipeline for approval
   and release.

## Validation loop
Run `validate_input` before and `validate_output` after. The output screen enforces: allowed
drafting status only; a packageable record renders all template sections, has no missing
components, a non-empty frontmatter block, and a passing metadata check; every readiness
claim is backed by a recorded approval and the tier's approvals are enumerated; no
release/publish/self-approval language; standing disclaimer present. See
[references/controls.md](references/controls.md). Correct and re-run until it passes or the
record is flagged not-packageable.

## Human approval
`external-delivery`. A human must review and authorize before a drafted package is published,
registered, or released into the catalog, or any system of record changes. This skill
proposes and drafts; it never publishes, never approves its own output, and never guarantees
a release. Internal drafting may be reviewer-sampled per
[references/controls.md](references/controls.md).

## Failure handling
- **Unknown archetype / absent metadata** → `needs-data`; map it to the build matrix first;
  do not guess the component set or allowed values.
- **Missing required component** → `missing-components`; list the missing component(s); never
  fabricate a file or mark it present to close a gap.
- **Incomplete / invalid / inconsistent metadata** → `metadata-incomplete`; a human corrects
  the frontmatter; never assemble on an inconsistent tier/action-mode/approval.
- **Unbacked readiness claim** → `unsupported-claim`; drop or substantiate the claim with a
  recorded approval; never assert validated/approved/released.
- **Tool timeout / stale standards** → return partial output with an explicit incomplete flag
  and the `build_standard_version` used; no retry assumption.

## Output contract
1. **Package queue** — per request: `skill_id`, `name`, `archetype`/`risk_tier`, `status`,
   and `packageable`.
2. **Authoring plan** (per packageable request) — identifiers, rendered frontmatter block,
   component checklist, source-map plan, approval checklist, and
   `reviewer_signoff_required: true`, following [assets/output-template.md](assets/output-template.md).
3. **Blocked list** — each non-packageable request with its itemized reason(s).
4. **Machine-readable** — the plan records keyed by `skill_id` with `build_standard_version`.
5. **Standing note** — "Draft skill package for owner review only; this skill does not
   publish, register, sign off, or release any skill into the catalog, does not approve its
   own output, and every package must pass validation and receive the required human
   approvals before release."

## Privacy and records
**Confidential.** Skill specs, domain artifacts, and approval records may reference
proprietary controls and thresholds; treat as internal. Never embed customer NPI/PII in a
drafted package or fixture — use de-identified fixtures under `evals/files/`. Retain the
drafted plan, `build_standard_version`, source citations, and the approval checklist with the
skill; log every read and every plan produced with the author identity.

## Gotchas
- **Drafting ≠ releasing.** The plan is a draft; a human/pipeline approves and publishes it.
  Never emit "published/registered/released/signed-off" language or imply the skill is live.
- **The skill never approves itself.** Required approvals are enumerated as owed/pending; the
  skill cannot record or grant them.
- **Archetype + tier drive the components.** The required component set and allowed values
  come from the standards; the wrong archetype produces the wrong package. Map unknowns first.
- **Every readiness claim needs a recorded approval.** A confident sentence with no approval
  behind it is an unsupported claim and is stripped by the output screen.
- **name == directory basename.** A drafted frontmatter whose name disagrees with the
  directory or the catalog is a fail-closed conflict.
- **Standards are a versioned contract.** Record `build_standard_version` on every plan so the
  component and metadata basis is reproducible and reviewable.
