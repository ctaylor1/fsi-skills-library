# Changelog — insurance-regulatory-filing-packager

## [0.1.0] — 2026-07-19
Initial authoring in the FSI Skills Library (baseline status: `new`; 2026 industry-expansion
cohort).

- **Scope:** deterministic completeness/consistency checks for a rate/form/rule filing —
  required-component completeness, required-exhibit presence, rate-change support, and
  effective-date notice lead — each gap located and cited; review-only disposition.
- **Controls:** R3 draft-only; NEVER submits/files with a regulator, approves or sets a rate, or
  certifies compliance; fail-closed on a missing checklist; `external-delivery` approval; NPI/PII
  masking.
- **Scripts:** `validate_input` (filing + checklist + components/exhibits), `calculate_or_transform`
  (deterministic gap checks), `validate_output` (citation coverage, review-only disposition,
  no-submit/approve/certify screen, disclaimer).
- **Evaluations:** trigger/routing, golden gaps (all four checks), clean-filing edge, deterministic
  script checks, no-submission safety + injection, external-delivery authorization.
- **Handoffs:** `actuarial-model-run-assistant`, `actuarial-data-lineage-checker`,
  `policy-wording-comparator`.

### Pending before release
- Product-filing / compliance owner review; checklist-config mapping sign-off per jurisdiction.
- Wire read-only filing-management (SERFF/equivalent) + actuarial-exhibit MCP integrations at deployment.
