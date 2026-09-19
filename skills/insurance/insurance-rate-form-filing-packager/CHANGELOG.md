# Changelog — insurance-rate-form-filing-packager

## [0.2.0] — 2026-09-18

- Phase 1: corrected implemented scope, source preservation, typed result states, portable evidence contract and substantive output recomputation.
- Added synthetic regression cases for observed correctness failures.
- Domain professional review and production integration acceptance remain pending.


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
- **Handoffs:** **Unavailable pricing/rate-adequacy specialist — refer to a qualified pricing actuary; do not substitute reserving**, `insurance-data-reconciler`,
  `policy-wording-comparator`.

### Pending before release
- Product-filing / compliance owner review; checklist-config mapping sign-off per jurisdiction.
- Wire read-only filing-management (SERFF/equivalent) + actuarial-exhibit MCP integrations at deployment.

## 0.2.1 — 2026-09-18

Align adjacent-workflow guidance with installed Phase 2/3 capabilities; native calculations and contract remain unchanged.
