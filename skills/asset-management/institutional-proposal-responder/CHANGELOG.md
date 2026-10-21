# Changelog

## 0.2.0 — 2026-09-20

- Adopt Phase 1 ownership and canonical naming; preserve alias metadata.
- Require source-bound native validation and document bounded support.
 — institutional-proposal-responder

## Unreleased — Phase 1 source fidelity

- Approval must be explicit; missing approval is unapproved. Library topic entries take precedence over prior answers. Future, undated and expired answers are withheld. Both embedded data_refs and question data_request dependencies must be dated, current and present. Performance-containing text without explicit data references is routed as a data gap. Only drafted responses carry text.
- Added detached original-input reconstruction and independent adverse-case regressions. Validation remains draft-only and does not authenticate sources or approvals.


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
  `conflicts-of-interest-reviewer`; upstream from `portfolio-performance-attributor`,
  `portfolio-exposure-analyzer`, `fund-fact-sheet-builder`; unsupported/stale/data-gap items
  routed to human content owners.

### Pending before release
- Product + compliance (marketing-rule) blind review; segregation-of-duty review of drafting
  vs. content approval vs. delivery.
- Confirm the controlled content library, required-disclosure register, and approval-broker
  source, owners, and versioning.
- Wire read-only MCP integrations (content library, policy retrieval, performance/risk data,
  approval broker) at deployment.

## Unreleased — Phase2 expanded mode

- Added explicit business mode with claim-level evidence, audience-safe ledgers and detached source reconstruction.
- Preserved original native input/output fixtures and legacy CLI behavior. No release or professional acceptance claimed.

- Require a named actor for a supplied RFP approval record; a blank actor cannot satisfy separation of duties.

- Treat approvals recorded after the knowledge cutoff or supporting source known_at as outstanding.
