# Changelog — lbo-model-builder

## [0.1.0] — 2026-07-18
Initial authoring in the FSI Skills Library (baseline status: `new`).

- **Scope:** deterministic source-linked LBO — Sources & Uses, a per-tranche debt schedule
  with cash sweep, a levered free-cash-flow forecast, liquidity, an exit walk, sponsor
  returns (MOIC / IRR), and base / upside / downside cases with model checks — as a draft
  for review.
- **Controls:** R2; no recommendation/guarantee/IC-approval; balanced Sources & Uses;
  assumptions carry provenance; MNPI handling; `external-delivery` approval.
- **Scripts:** `validate_input`, `calculate_or_transform` (deterministic LBO build),
  `validate_output` (S&U balance, debt/cash roll-forwards, exit and returns tie-outs,
  scenario monotonicity, no-advice screen, disclaimer).
- **Evaluations:** trigger/routing, golden model, deterministic script checks, no-advice +
  tie-out safety, external-delivery authorization.
- **Handoffs:** upstream `three-statement-model-builder`, `comps-analysis-builder`;
  downstream `valuation-reviewer`, `investment-committee-memo-builder`,
  `investment-banking-pitch-builder`, `due-diligence-packager`.

### Pending before release
- Domain SME (leveraged finance) blind review; entry/exit-multiple and financing-terms review.
- Wire read-only filings/market-data/data-room MCP integrations at deployment.
- Extend engine (post-baseline) for revolver draws, dividend recaps, and interim
  distributions where the deal structure requires them.
