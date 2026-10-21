# Changelog — dcf-modeler

## 0.2.0 — 2026-10-20

- Require detached original input for native output validation; reconstruct every result and reject omissions, alterations and extra fields. Guard finite numbers, shapes, dates, domains and duplicates; validate before computation.
- Only standalone-ratio-fcff forecasting is implemented. This method reforecasts from ratio drivers; it does not consume native three-statement rows or establish identical upstream forecasts. Every equity-bridge component must be explicit, finite, nonnegative and sourced, including genuine zeros; otherwise calculation is withheld. WACC weights must sum to one; invalid discounting/terminal domains fail input validation. No dividend/residual-income, NAV or financial-institution engine is implied.
- Regenerate synthetic positive and adversarial fixtures. Passing checks is not source authentication, professional acceptance or independent institutional assurance.


## [0.1.0] — 2026-07-18
Initial authoring in the FSI Skills Library (baseline status: `new`).

- **Scope:** deterministic source-linked DCF — forecast drivers, WACC, terminal value,
  enterprise-to-equity bridge, scenarios, sensitivities, and model checks — as a draft for
  review.
- **Controls:** R2; no recommendation/rating/price target; assumptions carry provenance;
  MNPI handling; `external-delivery` approval.
- **Scripts:** `validate_input`, `calculate_or_transform` (deterministic DCF build),
  `validate_output` (formula tie-outs, bridge checks, no-advice screen, disclaimer).
- **Evaluations:** trigger/routing, golden model, deterministic script checks, no-advice +
  tie-out safety, external-delivery authorization.
- **Handoffs:** downstream `scenario-sensitivity-generator`, `investment-banking-pitch-builder`,
  `company-profile-builder`, `due-diligence-packager`.

### Pending before release
- Domain SME (modeling) blind review; WACC/terminal-value assumption review.
- Wire read-only filings/market-data MCP integrations at deployment.

## 2026-09-20 — Category ownership migration

- Moved from Investment Banking & Research to Investment Research; stable skill ID retained.
- Native method and information/publication controls unchanged. Path alias is registered.

## 0.3.0 — 2026-10-20

Phase2 mode consumes explicit validated forecast_rows rather than reconstructing a constant-margin forecast. Each row must match issuer context financial basis, calendar annual dates and NOPAT/UFCF identities. Required wacc,terminal_growth,discounting,diluted_shares and explicit bridge values remain supplied assumptions. Mid-year applies to annual cash flows; terminal value is discounted to the end of the last forecast year. This is an annual nonfinancial corporate method only.
