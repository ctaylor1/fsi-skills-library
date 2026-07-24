# Changelog — payment-fraud-rule-impact-analyzer

## [0.1.0] — 2026-07-19
Initial authoring in the FSI Skills Library (baseline status: `new`; 2026 industry-expansion
cohort).

- **Scope:** deterministic fraud-rule impact estimate on a labeled sample — block counts,
  decline-rate delta, and the confusion-matrix shift (caught fraud, missed fraud, false positives)
  with deltas; both sides of the tradeoff reported; illustrative sample estimate.
- **Controls:** R3 model-and-calculate; NEVER deploys/enables/rolls out a rule and NEVER makes a
  live block/allow decision; unsupported op/field fails closed; labels never imputed; sample never
  extrapolated to production; `external-delivery` approval; PCI/NPI handling (txn ids, no PAN).
- **Scripts:** `validate_input` (rules + labeled sample + field presence), `calculate_or_transform`
  (rule eval + confusion), `validate_output` (confusion tie-outs, block-count ranges,
  no-deployment/no-decision screen, disclaimer).
- **Evaluations:** trigger/routing, golden impact (blocks/decline-delta/confusion-shift),
  unlabeled edge, deterministic script checks, no-deployment safety (language + confusion tie) +
  injection, external-delivery authorization.
- **Handoffs:** `payment-integration-readiness-pack`, `payment-api-log-diagnostic-pack`.

### Pending before release
- Payments risk/fraud owner review; rule-definition schema and sample-representativeness sign-off.
- Wire read-only labeled-sample + rule-definition MCP integrations at deployment.
