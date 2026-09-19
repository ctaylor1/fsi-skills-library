# Phase 1 — 0.2.0 (2026-09-18)

Added shared content-bound evidence states, strict financial/date handling, input-aware output validation and adverse regressions. Withhold comparisons across mismatched bases; preserve prior duplicates, zero-baseline movements, removed observations and non-evaluable checks.

Forward-evaluation fixes: retain all duplicate member references, values and bases; report independently observed basis conflicts alongside duplicates; inspect every current row for definition-baseline changes. Added evidence-retention and combined-conflict regressions and refreshed the positive output.

# Changelog — insurance-data-reconciler

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
- **Handoffs:** `pc-reserving-analysis-assistant`, `pc-reserving-analysis-assistant`.

### Pending before release
- Appointed-actuary / data-steward control-owner review; definition-registry + threshold config sign-off.
- Wire read-only policy-admin/claims/actuarial + definition-registry MCP integrations at deployment.
