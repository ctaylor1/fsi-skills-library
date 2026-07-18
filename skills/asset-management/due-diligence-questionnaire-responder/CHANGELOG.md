# Changelog — due-diligence-questionnaire-responder

## [0.1.0] — 2026-07-17
Initial authoring in the FSI Skills Library (baseline status: `new`). Created to draft DDQ/RFP
responses **only from approved content**, keeping content authoring, compliance review, and
external delivery as distinct human-owned controls.

- **Scope:** match each questionnaire question to a single approved content-library or prior
  answer, set a response status (`drafted`, `stale`, `unapproved-source`, `data-gap`,
  `unsupported`), attach owner + effective date + citations, inject required disclosures,
  capture approvals, and route open questions to owners. Draft-only; no send/submit.
- **Controls:** R2, external-delivery approval; approved-source gate (no drafting from
  draft/in-review/expired content); no fabricated answers or figures; standard performance
  disclosure required when data is cited; no performance/return guarantees; no
  completeness/final overclaim; `draft_status: draft-assembled`; versioned content/disclosure/
  template contracts.
- **Assets:** `assets/output-template.md` (`ddq-response-template@0.1.0`) mirroring the
  canonical `sections` enforced by `validate_output`.
- **Scripts:** `validate_input` (intake schema, unsupported/ambiguous/stale/data-gap warnings),
  response assembler (matching + status + disclosures + approvals + source index),
  `validate_output` (required sections, citation + approved-source on every asserted answer,
  fabrication guard, performance-disclosure presence, approval completeness, prohibited
  delivery/guarantee/overclaim language, draft-status, standing note).
- **Evaluations:** trigger/routing, golden 9-question DDQ exercising every status, deterministic
  script checks, no-fabrication/no-delivery safety fixture (`validate_output` exit 1), prompt
  injection and performance-guarantee refusals, delivery-authorization refusal.
- **Handoffs:** downstream to `communications-compliance-reviewer` and
  `conflicts-of-interest-reviewer`; upstream from `performance-attribution-builder`,
  `portfolio-exposure-analyzer`, `fund-fact-sheet-builder`; unsupported/stale/data-gap items
  routed to human content owners.

### Pending before release
- Product + compliance (marketing-rule) blind review; segregation-of-duty review of drafting
  vs. content approval vs. delivery.
- Confirm the controlled content library, required-disclosure register, and approval-broker
  source, owners, and versioning.
- Wire read-only MCP integrations (content library, policy retrieval, performance/risk data,
  approval broker) at deployment.
