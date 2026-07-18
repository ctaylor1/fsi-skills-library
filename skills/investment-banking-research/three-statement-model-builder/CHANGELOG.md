# Changelog — three-statement-model-builder

## [0.1.0] — 2026-07-18
Initial authoring in the FSI Skills Library (baseline status: `new`).

- **Scope:** deterministic, source-linked three-statement operating model — a linked income
  statement, balance sheet, and cash-flow statement with debt, PP&E, and working-capital
  schedules, base/upside/downside scenarios, and independent tie-outs — as a draft for review.
- **Controls:** R2; no recommendation/rating/price target/valuation; every driver carries a
  source; MNPI handling; `external-delivery` approval.
- **Scripts:** `validate_input`, `calculate_or_transform` (deterministic non-circular model
  build, cash as the plug), `validate_output` (balance-sheet identity, cash tie, equity and
  PP&E roll-forwards re-derived independently, scenario monotonicity, provenance,
  reproducibility, no-advice screen, disclaimer).
- **Evaluations:** trigger/routing, golden model, deterministic script checks, tie-out +
  no-advice safety on a non-compliant fixture, external-delivery authorization.
- **Handoffs:** downstream `dcf-modeler`, `lbo-model-builder`, `merger-model-builder`,
  `comps-analysis-builder`, `scenario-sensitivity-generator`, `valuation-reviewer`.

### Pending before release
- Domain SME (modeling) blind review; driver and scenario-delta assumption review.
- Wire read-only filings/market-data/operating-model MCP integrations at deployment.
