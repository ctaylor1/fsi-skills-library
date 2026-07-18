# Changelog — contract-obligation-extractor

## [0.1.0] — 2026-07-17
Initial authoring in the FSI Skills Library (baseline status: `new`). Created to turn an
executed contract into a source-linked, clause-cited **draft obligation register** for legal
operations, procurement, and business owners — separating extraction from legal interpretation,
obligation monitoring, and external delivery (distinct controls, entitlements, and
accountability).

- **Scope:** extract obligations, key dates, service levels, rights, restrictions, renewal and
  termination terms, data terms, and dependencies into one register, each item mapped to its
  governing clause with a citation. Draft-only; no system-of-record change.
- **Controls:** R2, `external-delivery`; no legal advice/interpretation, no completeness or
  silence claims, no unsupported (uncited) assertions, no fabrication, and no send/submit/
  sign/execute/deliver; absence of a clause is a `coverage-gap` to confirm; conflicts and
  ambiguities are surfaced for humans, never resolved here; versioned taxonomy/template/config.
- **Archetype (Draft & package):** `assets/output-template.md` defines the register sections;
  `validate_output` enforces template fidelity, a clause citation on every asserted item (no
  unsupported assertions), recorded human reviews (role/date/citation) with the delivery
  approval gate flagged, the draft `assembly_status`, and the legal-advice/completeness/delivery
  language screens.
- **Scripts:** `validate_input` (intake schema; unsourced/coverage-gap/missing-review
  warnings), assembler (`calculate_or_transform`: status assignment, section routing, review
  capture, cited source index), `validate_output` (required sections, citation coverage, review
  capture, forbidden-language screens, draft status, standing note).
- **Evaluations:** trigger/routing, golden register exercising every status (extracted,
  ambiguous, conflict, unsourced, coverage-gap) plus recorded/outstanding reviews, deterministic
  script checks, and safety fixtures for legal-advice/completeness/delivery language, prompt
  injection, and fabrication.
- **Handoffs:** downstream to `covenant-compliance-monitor`, `third-party-risk-assessor`, and
  `meeting-action-tracker`; upstream from `procurement-sourcing-assistant`; legal
  interpretation, negotiation, execution, and delivery to licensed counsel / a human via the
  approval broker.

### Pending before release
- Legal-operations and privacy control-owner blind review; confirm the obligation taxonomy,
  register template, and required-review set (source, owner, versioning).
- Confirm masking/retention against the organization's contract recordkeeping and data-residency
  policy.
- Wire read-only MCP integrations (contract/CLM, document-intelligence, taxonomy, vendor-master)
  at deployment.
