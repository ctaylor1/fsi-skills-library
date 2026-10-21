# Changelog

## 0.2.0 — 2026-09-20

- Adopt Phase 1 ownership and canonical naming; preserve alias metadata.
- Require source-bound native validation and document bounded support.
 — fund-liquidity-assessor

## Unreleased — Phase 1 integrity repairs

- Added complete original-input binding and reconstruction checks; native output does not authenticate sources or accept unreviewed extra fields.
- Repaired bounded calculation/input contracts and documented unsupported cases in references/phase1-contract.md.
- Updated synthetic golden fixtures and native evaluation commands; added cross-package behavioral regressions.

## [0.1.0] — 2026-07-17
Initial authoring in the FSI Skills Library (baseline status: `new`).

- **Scope:** explainable liquidity metrics under transparent, fully parameterized scenarios +
  cited evidence + a suggested liquidity-risk band. Read-only; no decision, no trade, no
  fund-liquidity action, no breach determination.
- **Metrics (deterministic):** redemption-coverage shortfall/thin, full-liquidation horizon
  exceeded, collateral-buffer shortfall, elevated liquidation cost, and illiquid concentration
  — each explainable and evidenced from a participation-of-ADV liquidation model (see
  `scripts/calculate_or_transform.py`).
- **Controls:** R2; hard boundary against trading/liquidation instructions, fund-liquidity
  actions (gate/suspend/side-pocket/swing pricing), mandate-breach determinations, and
  investment advice; versioned-config thresholds only; mandatory scenario-assumption
  disclosure; modeling caveats required; `external-delivery` approval.
- **Scripts:** `validate_input` (portfolio/scenario schema, evaluability warnings), liquidity
  engine, `validate_output` (evidence/citation completeness, deterministic band tie-out,
  scenario-transparency check, recommendation/action/determination-language screen, disclaimer,
  caveats).
- **Evaluations:** trigger/routing, golden Stressed case, baseline-adequate edge, deterministic
  script checks, no-action/no-determination safety + injection, external-delivery authorization.
- **Handoffs:** downstream to `investment-mandate-reviewer`, `counterparty-exposure-monitor`,
  `investment-committee-memo-builder`, `investment-commentary-builder`,
  `institutional-proposal-responder`; upstream from `portfolio-exposure-analyzer`.

### Pending before release
- Domain SME (liquidity risk) + control-owner blind review; model-risk review of the
  participation-of-ADV and cost models and thresholds.
- Confirm the versioned threshold/band config source and scenario library owner.
- Wire read-only MCP integrations (PMS/OMS, market data, risk/performance, config, scenario) at
  deployment.
