# Changelog — policy-document-assistant

## [0.1.0] — 2026-07-17
Initial authoring in the FSI Skills Library (baseline status: `new`). Created as a Draft &
package copilot that assembles controlled policy/procedure drafts from an approved
requirements register, with source mapping, deterministic versioning/review cadence, change
summaries, and recorded approvals.

- **Scope:** draft / amend / compare / explain controlled policies and procedures. Draft-only
  (R2); no publication, activation, effective-dating, or system-of-record write.
- **Controls:** every normative statement maps to an `approved` requirement (no unsupported
  assertions); required sections enforced (template fidelity); version bump and next-review
  date tie out to the versioned policy-standard rules; owner/legal/compliance approvals must
  be recorded before external delivery; no self-recorded or backdated approvals.
- **Scripts:** `validate_input` (build-request schema, unsupported-clause and data-gap
  warnings), `calculate_or_transform` (deterministic draft assembly: section layout, source
  resolution, version bump, tier review cadence, change summary), `validate_output` (required
  sections, unsupported-assertion screen, recorded-approvals check, version/review tie-out,
  publication-language screen, standing note).
- **Assets:** `assets/output-template.md` — the controlled policy draft template.
- **Evaluations:** trigger/routing, a golden CIP draft exercising every section, deterministic
  self-tests, and a non-compliant fixture that fails output validation (missing section,
  unsupported clause, missing approval, publication language); plus injection, no-unsupported,
  no-publish, and self-approval refusals.
- **Handoffs:** upstream from `regulatory-change-impact-analyzer`, `policy-procedure-gap-analyzer`,
  `contract-obligation-extractor`; downstream to `policy-procedure-gap-analyzer`,
  `board-committee-pack-builder`, `regulatory-exam-response-packager`, `knowledge-base-curator`.
  Approval and publication are human/operations actions.

### Pending before release
- Policy-owner + legal + compliance blind review of the template and clause-sourcing rule.
- Confirm the requirements-register and `config:policy-std` source, owner, and versioning
  (version-bump rule, tier review cadence, required-approval matrix).
- Wire read-only MCP integrations (requirements register, controlled content library,
  approved-source retrieval, document intelligence, entity resolution) at deployment.
