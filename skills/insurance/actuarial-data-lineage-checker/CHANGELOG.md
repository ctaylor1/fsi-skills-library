# Changelog — actuarial-data-lineage-checker

## [0.1.0] — 2026-07-19
Initial authoring in the FSI Skills Library (baseline status: `new`; 2026 industry-expansion
cohort).

- **Scope:** deterministic reconciliation of actuarial input data across periods/sources —
  duplicates, missing periods, definition/version shifts, unexplained movement, new series —
  with cited lineage; review-only disposition.
- **Controls:** R2 reconcile-only; NEVER alters/corrects source data, selects assumptions/methods,
  runs a model, or certifies reserve data; guards division by zero prior; `external-delivery`
  approval.
- **Scripts:** `validate_input` (schema, evaluability), `calculate_or_transform` (deterministic
  break detection + lineage), `validate_output` (break citation coverage, review-only disposition,
  no-alter/no-certify screen, disclaimer).
- **Evaluations:** trigger/routing, golden all-break-types case, zero-prior edge, deterministic
  script checks, no-alter/certify safety + injection, external-delivery authorization.
- **Handoffs:** `actuarial-model-run-assistant`, `reserving-analysis-assistant`.

### Pending before release
- Appointed-actuary / data-steward control-owner review; definition-registry + threshold config sign-off.
- Wire read-only policy-admin/claims/actuarial + definition-registry MCP integrations at deployment.
