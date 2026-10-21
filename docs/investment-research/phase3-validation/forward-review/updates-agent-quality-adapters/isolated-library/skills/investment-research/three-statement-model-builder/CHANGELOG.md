# Changelog — three-statement-model-builder

## 0.2.0 — 2026-10-20

- Require detached original input for native output validation; reconstruct every result and reject omissions, alterations and extra fields. Guard finite numbers, shapes, dates, domains and duplicates; validate before computation.
- Explicit base/upside/downside deltas are required; no default scenario is invented. This annual nonfinancial corporate model uses constant drivers, opening-debt interest and scheduled repayment without a borrowing/revolver engine. Negative cash is reported as a funding gap; all_balanced describes accounting identities only. No financial-sector or REIT engine is implemented.
- Regenerate synthetic positive and adversarial fixtures. Passing checks is not source authentication, professional acceptance or independent institutional assurance.


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

## 2026-09-20 — Category ownership migration

- Moved from Investment Banking & Research to Investment Research; stable skill ID retained.
- Native method and information/publication controls unchanged. Path alias is registered.

## 0.3.0 — 2026-10-20

Phase2 mode uses schema_version ir-phase2/1.0 plus the full common evidence context, explicit issuer_type nonfinancial-corporate, accounting_basis, consolidation_scope, fiscal_calendar calendar and model_input containing the original native schema with company_id matching the issuer. forecast_rows are generated from every integrated year: calendar dates, EBIT, depreciation, capex, change in operating noncash working capital, tax rate, NOPAT and UFCF. No flat-margin reconstruction is used. Funding gaps remain unresolved and no new financing engine is supplied.
