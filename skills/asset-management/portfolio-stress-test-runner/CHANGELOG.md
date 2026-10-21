# Changelog

## 0.2.0 — 2026-09-20

- Adopt Phase 1 ownership and canonical naming; preserve alias metadata.
- Require source-bound native validation and document bounded support.
 - portfolio-stress-test-runner

## Unreleased — Phase 1 integrity repairs

- Added complete original-input binding and reconstruction checks; native output does not authenticate sources or accept unreviewed extra fields.
- Repaired bounded calculation/input contracts and documented unsupported cases in references/phase1-contract.md.
- Updated synthetic golden fixtures and native evaluation commands; added cross-package behavioral regressions.

## [0.1.0] - 2026-07-20
Initial authoring in the FSI Skills Library (baseline status: `new`).

- **Scope:** deterministic portfolio stress-test runner - execute human-approved
  historical/hypothetical scenarios against an approved portfolio and risk-factor model,
  compute scenario P&L and stressed value, attribute drivers by position and by factor,
  reconcile to the approved stress engine, and emit a reproducible run - as a draft for
  review.
- **Controls:** R2; never invents/designs/edits a scenario (approved source only); no
  investment recommendation, hedge/rebalance/de-risk instruction, risk-limit, or capital
  determination; assumptions carry provenance and scenarios carry approval; MNPI handling;
  `external-delivery` approval.
- **Scripts:** `validate_input` (schema + HARD BOUNDARY approved-scenario screen),
  `calculate_or_transform` (deterministic first-order + convexity revaluation, position/factor
  attribution, engine reconciliation, reproducibility hash), `validate_output` (independent
  tie-outs, reconciliation, approved-scenario/provenance screen, no-advice screen, disclaimer).
- **Evaluations:** trigger/routing, golden two-scenario run, deterministic script checks,
  non-compliant-pack and un-approved-scenario safety fixtures (fail closed), prompt-injection,
  and external-delivery authorization.
- **Handoffs:** upstream `stress-test-scenario-designer` (approved scenarios) and
  `portfolio-holdings-summarizer` / risk model (positions, sensitivities); parallel
  `portfolio-exposure-analyzer`, `portfolio-risk-contribution-analyzer`,
  `scenario-sensitivity-generator`; downstream `market-risk-limit-monitor`,
  `portfolio-characteristics-change-monitor`.

### Pending before release
- Domain SME (market/portfolio risk) blind review; sensitivity-model and scenario-set
  approval review.
- Wire read-only portfolio, risk-factor-model, approved-scenario-library, and approved-stress-
  engine MCP integrations at deployment.
