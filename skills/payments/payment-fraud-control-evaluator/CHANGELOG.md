# [0.3.0] — 2026-09-18

Payments Phase 3: Design payment journey and threat control options, and replay baseline/proposed multi-rule portfolios over supplied transactions with mature-label, value, friction and rule-interaction analysis. Preserve the separate legacy single-predicate comparison. Draft decision support only; never deploy controls or decide a live payment.

Adds source-bound portable domain CLIs, normalized synthetic fixtures, negative/action/tamper checks and adversarial regressions. Source research reviewed as orientation; specialist, legal/model-risk where applicable, source authentication, accessibility and production acceptance remain pending. No approvals are inferred from tests.

# Phase 1 — 2026-09-17

Corrected executable scope, evidence boundaries and/or naming; bundled canonical payment contract. Tests establish bounded offline behavior, not professional or deployment acceptance. See docs/payments/PHASE1-IMPLEMENTATION.md at repository level.

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
