# Changelog

## 0.2.0 — 2026-09-20

- Adopt Phase 1 ownership and canonical naming; preserve alias metadata.
- Require source-bound native validation and document bounded support.
 — portfolio-hedge-reviewer

## Unreleased — Phase 1 integrity repairs

- Added complete original-input binding and reconstruction checks; native output does not authenticate sources or accept unreviewed extra fields.
- Repaired bounded calculation/input contracts and documented unsupported cases in references/phase1-contract.md.
- Updated synthetic golden fixtures and native evaluation commands; added cross-package behavioral regressions.

## [0.1.0] — 2026-07-20
Initial authoring in the FSI Skills Library (baseline status: `new`).

- **Scope:** deterministic first-order hedge-analysis support packet — portfolio exposures /
  sensitivities, residual exposure and coverage per candidate hedge, supplied cost, scenario
  P&L (portfolio / hedge / hedged), reconciliation to approved-engine totals, tie-outs, and
  limitations — as a neutral comparison for review.
- **Controls:** R2; no hedge selection / recommendation / ranking; no hedge decision or
  sizing; no trade execution or staging; no advice or efficacy guarantee; assumptions carry
  provenance; MNPI handling; `external-delivery` approval; durable `case_id` / `packet_id`.
- **Scripts:** `validate_input`, `calculate_or_transform` (deterministic exposure/scenario
  engine, self-verifying `--selftest`), `validate_output` (residual/coverage/scenario
  tie-outs, approved-engine reconciliation, provenance, tier-boundary screen, disclaimer).
- **Evaluations:** trigger/routing (exposure, pricing-hedging, stress, risk-contribution,
  limit, IC-memo), golden comparison, deterministic script checks, two fail-closed safety
  fixtures (non-compliant packet + non-compliant input), prompt-injection and
  external-delivery authorization.
- **Handoffs:** upstream `portfolio-exposure-analyzer`, `pricing-hedging-scenario-calculator`,
  `stress-test-scenario-designer`; parallel `portfolio-stress-test-runner`,
  `portfolio-risk-contribution-analyzer`, `market-risk-limit-monitor`,
  `transaction-cost-estimator`; downstream `investment-committee-memo-builder`; human hedge
  decision (PM / IC) and execution (trading desk / OMS).

### Pending before release
- Domain SME (market risk / model governance) blind review; sensitivity-convention and
  factor-unit review; reconciliation-tolerance sign-off.
- Wire read-only risk-engine / model-registry / scenario-library MCP integrations at
  deployment.


## 0.3.0 — 2026-10-04

Added explicitly selected advanced-derivatives review using supplied full-repricing engine and independent benchmark contracts, exact scenario differences and source-bound reconstruction. Existing no-extension schema, fixtures and first-order behavior are retained. No pricing engine or trade action is executed.
