# Changelog

## 0.2.0 — 2026-09-20

- Adopt Phase 1 ownership and canonical naming; preserve alias metadata.
- Require source-bound native validation and document bounded support.
 — portfolio-exposure-analyzer

## Unreleased — Phase 1 integrity repairs

- Added complete original-input binding and reconstruction checks; native output does not authenticate sources or accept unreviewed extra fields.
- Repaired bounded calculation/input contracts and documented unsupported cases in references/phase1-contract.md.
- Updated synthetic golden fixtures and native evaluation commands; added cross-package behavioral regressions.

## [0.1.0] — 2026-07-17
Initial authoring in the FSI Skills Library (baseline status: `new`).

- **Scope:** explainable portfolio exposures across issuer, sector, country, currency, asset
  class, duration, liquidity, factor, and look-through holdings + a documented
  concentration-limit screen + suggested review priority. Read-only; no compliance
  determination, no trade/portfolio action.
- **Exposures (deterministic):** look-through decomposition of pooled vehicles; per-dimension
  aggregation with cited contributing rows; sovereign/cash issuer-and-sector exemptions and
  home-country exemption; FI-sleeve modified duration; days-to-liquidate buckets; factor
  exposure when loadings are present (see `scripts/calculate_or_transform.py`).
- **Controls:** R2; hard boundary against mandate-compliance determination, trade/rebalance/
  hedge/divestment, and personalized investment advice; versioned-config limits only;
  considerations required; `external-delivery` approval.
- **Scripts:** `validate_input` (holdings schema, evaluability warnings), exposure engine,
  `validate_output` (evidence/citation completeness, deterministic priority tie-out,
  determination/action/advice screen, disclaimer, considerations).
- **Evaluations:** trigger/routing, golden Elevated case (look-through issuer + sector +
  illiquidity findings), missing-liquidity edge, deterministic script checks, no-determination
  safety + injection, external-delivery authorization.
- **Handoffs:** downstream to `investment-mandate-reviewer`, `fund-liquidity-assessor`,
  `counterparty-exposure-monitor`, `portfolio-performance-attributor`, `investment-commentary-builder`,
  `fund-fact-sheet-builder`, `investment-committee-memo-builder`.

### Pending before release
- Domain SME (portfolio risk) + control-owner blind review; conduct review of exposure
  framing (active vs absolute).
- Confirm the versioned limits/exemption/priority config source and its owner.
- Wire read-only MCP integrations (PMS/OMS, market/reference data, look-through, risk model,
  config) at deployment.
