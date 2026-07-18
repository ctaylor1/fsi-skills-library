# Changelog — dcf-modeler

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
