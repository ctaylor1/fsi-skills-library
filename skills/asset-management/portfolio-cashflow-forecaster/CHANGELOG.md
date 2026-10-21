# Changelog

## 0.2.0 — 2026-09-20

- Adopt Phase 1 ownership and canonical naming; preserve alias metadata.
- Require source-bound native validation and document bounded support.
 — portfolio-cashflow-forecaster

## Unreleased — Phase 1 integrity repairs

- Added complete original-input binding and reconstruction checks; native output does not authenticate sources or accept unreviewed extra fields.
- Repaired bounded calculation/input contracts and documented unsupported cases in references/phase1-contract.md.
- Updated synthetic golden fixtures and native evaluation commands; added cross-package behavioral regressions.

## [0.1.0] — 2026-07-20
Initial authoring in the FSI Skills Library (baseline status: `new`).

- **Scope:** deterministic, source-linked liquidity cash-flow forecast — aggregate
  subscriptions, redemptions, coupons, dividends, maturities, collateral, and known funding needs
  into dated buckets, roll opening cash forward under analyst-supplied scenarios, and emit a dated
  ladder (net flow, closing balance, cumulative net, first-shortfall bucket) with a
  provenance-tagged assumptions log and optional approved-engine reconciliation — as a draft for
  review.
- **Controls:** R2; no scenario choice, no asset-sale/cash-raising recommendation, no
  liquidity-buffer setting, no redemption gating/guarantee; every input carries provenance; MNPI
  handling; `external-delivery` approval.
- **Scripts:** `validate_input`, `calculate_or_transform` (deterministic dated-ladder build),
  `validate_output` (formula tie-outs, reconciliation, provenance, no-decision/advice screen,
  disclaimer).
- **Evaluations:** trigger/routing, golden two-scenario forecast, deterministic script checks,
  no-decision + tie-out + reconciliation safety, prompt-injection, and external-delivery
  authorization.
- **Handoffs:** stressed-liquidation to `fund-liquidity-assessor`; treasury/ALM survival-horizon
  to `liquidity-risk-scenario-analyzer` (distinct R3); downstream `investment-committee-memo-builder`,
  `board-committee-pack-builder`, `investment-mandate-reviewer`.

### Pending before release
- Domain SME (fund liquidity-risk) blind review; scenario/reconciliation convention review.
- Wire read-only transfer-agent / custodian / collateral / market-data MCP integrations at deployment.
