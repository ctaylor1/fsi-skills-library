# Changelog — portfolio-exposure-analyzer

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
- **Handoffs:** downstream to `mandate-compliance-monitor`, `liquidity-stress-analyzer`,
  `counterparty-exposure-monitor`, `performance-attribution-builder`, `fund-commentary-drafter`,
  `fund-fact-sheet-builder`, `investment-committee-memo-builder`.

### Pending before release
- Domain SME (portfolio risk) + control-owner blind review; conduct review of exposure
  framing (active vs absolute).
- Confirm the versioned limits/exemption/priority config source and its owner.
- Wire read-only MCP integrations (PMS/OMS, market/reference data, look-through, risk model,
  config) at deployment.
