# Changelog — portfolio-cashflow-liquidity-forecaster

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
- **Handoffs:** stressed-liquidation to `liquidity-stress-analyzer`; treasury/ALM survival-horizon
  to `liquidity-risk-scenario-analyzer` (distinct R3); downstream `investment-committee-memo-builder`,
  `board-committee-pack-builder`, `mandate-compliance-monitor`.

### Pending before release
- Domain SME (fund liquidity-risk) blind review; scenario/reconciliation convention review.
- Wire read-only transfer-agent / custodian / collateral / market-data MCP integrations at deployment.
