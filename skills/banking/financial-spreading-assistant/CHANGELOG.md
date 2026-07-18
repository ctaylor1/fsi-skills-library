# Changelog — financial-spreading-assistant

## [0.1.0] — 2026-07-17
Initial authoring in the FSI Skills Library (baseline status: `new`).

- **Scope:** deterministic, source-linked credit spread — classify borrower statement/tax-return
  line items to a standard taxonomy, spread into balance-sheet and income-statement subtotals per
  period, compute leverage/liquidity/coverage/profitability ratios and an operating cash-flow
  proxy, produce an as-reported vs. normalized (add-back) view, and tie out to the borrower's
  reported totals. Draft-only; no credit decision, no advice, no system-of-record write.
- **Model (deterministic):** taxonomy classification with an ambiguous-mapping escalation queue,
  subtotal aggregation, documented ratio formulas (with zero-denominator guards), indirect
  operating cash-flow proxy, documented income-statement add-backs applied to a normalized view,
  and period-over-period trends (see `scripts/calculate_or_transform.py`).
- **Controls:** R2; hard boundary against credit decisions / ratings / eligibility, facility
  recommendations, and investment/tax advice; versioned taxonomy, classification map, and ratio
  formulas only; ambiguous mappings escalated (never guessed); tie-outs never plugged; add-back
  provenance + citations required; `external-delivery` approval.
- **Scripts:** `validate_input` (schema, ambiguous-mapping / thin-input / missing-anchor
  warnings), spreading engine, `validate_output` (re-derived balance and reported tie-outs, net
  income tie, as-reported-vs-normalized behaviour, add-back provenance/citation, ambiguous-mapping
  escalation, reproducibility, no-decision/advice screen, disclaimer).
- **Evaluations:** trigger/routing, a golden two-year spread with fixed ratios/tie-outs, an
  ambiguous-mapping golden, deterministic script checks, a non-compliant output safety fixture
  (`validate_output` exits 1), no-decision safety + injection, and external-delivery authorization.
- **Handoffs:** downstream to `credit-memo-drafter`, `covenant-compliance-monitor`,
  `cashflow-forecaster`, `loan-affordability-precheck`, `credit-application-packager`,
  `loan-package-completeness-checker`; upstream from `customer-onboarding-document-checker` and
  `bank-statement-analyzer`; sibling boundary with `financials-normalizer`.

### Pending before release
- Domain SME (commercial credit / spreading) + control-owner blind review; conduct review of
  classification and add-back presentation.
- Confirm the versioned template, classification-map, and ratio/tolerance config sources and their
  owner; wire the approved ratio/covenant definitions used by the deploying institution.
- Wire read-only MCP integrations (document intelligence, template/taxonomy, loan origination,
  config) at deployment.
