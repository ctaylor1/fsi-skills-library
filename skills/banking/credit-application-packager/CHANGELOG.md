# Changelog — credit-application-packager

## [0.1.0] — 2026-07-17
Initial authoring in the FSI Skills Library (baseline status: `new`). Created to separate
credit-application **packaging** (assemble, index, flag open items) from formal completeness
**certification** and from credit **decisioning** — distinct controls, entitlements, and
accountability.

- **Scope:** map required package components to supporting documents, assign a deterministic
  assembly status (`included` / `stale` / `unresolved` / `open-item`), check borrower/entity
  consistency, capture recorded approvals and outstanding required approvals, list outstanding
  conditions, and build a cited source index. Draft-only; no system-of-record change.
- **Controls:** R2; `external-delivery` approval; never makes a credit decision, adverse
  action, or completeness certification; never fabricates a missing document; never sends,
  submits, files, or delivers; identity mismatches left `unresolved` (no auto-merge); approvals
  recorded, never assumed; versioned `required_components` / `required_approvals` / template.
- **Scripts:** `validate_input` (intake schema, open-item/freshness/consistency warnings),
  `calculate_or_transform` (deterministic package assembler → manifest), `validate_output`
  (required sections, no unsupported claims, approvals recorded, no decision/certification/
  delivery language, draft status, standing note).
- **Assets:** `output-template.md` (credit-package-template@0.1.0) — the human-facing package
  render whose sections mirror the enforced manifest sections.
- **Evaluations:** trigger/routing, golden 5-component intake exercising every assembly status
  and approval/condition path, deterministic script checks, and a safety fixture that fails
  closed on credit-decision / completeness-certification / delivery language and uncited
  claims; injection, fabrication, and delivery-authorization refusals.
- **Handoffs:** downstream to `loan-package-completeness-checker` (certification),
  `credit-memo-drafter` (memo), `covenant-compliance-monitor` (ongoing); upstream from
  `financial-spreading-assistant`, `bank-statement-analyzer`,
  `customer-onboarding-document-checker`. Credit decision and external delivery are human-owned.

### Pending before release
- Banking product & credit-operations control-owner review; segregation-of-duty review
  (packaging vs. certification vs. decisioning).
- Confirm the per-product/jurisdiction `required_components` and `required_approvals` source,
  owner, and versioning.
- Wire read-only MCP integrations (LOS, document intelligence, core banking, CRM, product
  terms) at deployment.
