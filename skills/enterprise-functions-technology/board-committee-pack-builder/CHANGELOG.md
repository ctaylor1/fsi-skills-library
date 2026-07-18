# Changelog — board-committee-pack-builder

## [0.1.0] — 2026-07-18
Initial authoring in the FSI Skills Library (baseline status: `new`). Created to assemble
controlled board/committee packs as an auditable DRAFT, cleanly separated from the skills
that produce the underlying content and from the humans who approve and deliver the pack.

- **Scope:** organize decisions/resolutions, a metrics/KPI dashboard, risks, issues and
  matters arising, the approved-source register, an approvals register, and concise page
  takeaways into a template-faithful draft with every claim mapped to a source. Draft-only;
  no system-of-record change.
- **Controls:** R2; external-delivery approval; never sends/submits/distributes/finalizes;
  never self-approves a decision; no unsupported assertions; figures cited with `as_of`
  dates; `template_version` treated as a versioned contract.
- **Scripts:** `validate_input` (pack-request schema, unresolved-source and unsourced-item
  warnings), `calculate_or_transform` (resolve citations, build approvals register, compute
  completeness and unsupported_claims), `validate_output` (template fidelity, no unsupported/
  unapproved claims, required approvals recorded, draft-only screen, standing note).
- **Assets:** `output-template.md` defining the required pack sections.
- **Evaluations:** trigger/routing, golden pack assembly exercising sourcing and both
  proposed and human-approved decisions, deterministic script checks, a non-compliant-pack
  safety check (missing section, unsupported claim, self-approved decision, delivery
  language) that must fail closed, plus draft-only / no-self-approve refusals.
- **Handoffs:** upstream from `management-reporting-packager`,
  `enterprise-risk-assessment-builder`, `key-risk-indicator-monitor`,
  `regulatory-change-impact-analyzer`, `investment-committee-memo-builder`,
  `policy-document-assistant`, `enterprise-meeting-preparer`; downstream to
  `meeting-action-tracker`; approval and delivery to humans.

### Pending before release
- Corporate-secretary / governance control-owner blind review; company-secretary and legal
  review of approval-routing and disclosure handling.
- Confirm the approved board-pack template revision, its owner, and the source register
  mapping for each committee type (audit, risk, board).
- Wire read-only MCP integrations (controlled content/templates, management reporting,
  risk register/KRI, action tracking, documents) at deployment.
