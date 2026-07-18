# Changelog — fsi-skill-authoring-assistant

## [0.1.0] — 2026-07-17
Initial authoring in the FSI Skills Library (baseline status: `new`). Created as the skill
engineering copilot that drafts and validates FSI Agent Skill packages, keeping authoring
separate from review, approval, and release (distinct roles and segregation of duties).

- **Scope:** from an approved spec, resolve required components (archetype + tier), assemble
  specification-valid frontmatter and the standard body sections, wire deterministic
  validation/eval scripts, and render a review-ready authoring plan. Draft-only; publishing,
  registration, and release are out of scope.
- **Controls:** R2; no publish/register/release into the catalog; no self-approval; no
  fabricated metadata, sources, evaluations, or approval records; readiness claims must be
  backed by recorded approvals; release/approval-overclaim language screen; versioned build
  standard / metadata schema / catalog contract.
- **Scripts:** `validate_input` (build-request schema, name/directory tie-out, needs-data
  warnings), package planner (`calculate_or_transform`: required-component diff, metadata
  completeness/allowed-value/consistency checks, approvals owed, claim-vs-approval test,
  status precedence), `validate_output` (allowed statuses, template fidelity + component
  completeness, metadata check, unsupported-claim + approvals enumerated,
  release/self-approval language screen, standing note).
- **Evaluations:** trigger/routing, golden 5-request queue exercising every status
  (draft-package, metadata-incomplete, missing-components, unsupported-claim, needs-data),
  deterministic script checks, no-publish / no-self-approval / no-fabrication safety, and a
  release-authorization refusal; a non-compliant `plan_bad.json` trips the output guardrail.
- **Handoffs:** upstream from portfolio governance / build standards / catalog / SMEs;
  downstream to the release pipeline / catalog owner and named human approvers (no skill
  performs the release).

### Pending before release
- Product-owner + domain-SME + control-owner blind review; segregation-of-duty review
  (authoring vs. approval vs. release).
- Confirm the build-standard / metadata-schema / catalog source, owner, and versioning.
- Wire read-only MCP integrations (standards/schema, catalog, knowledge, templates, developer
  tooling, approval records) at deployment.
