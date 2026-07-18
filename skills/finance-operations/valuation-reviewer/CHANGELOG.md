# Changelog — valuation-reviewer

## [0.1.0] — 2026-07-17
Initial authoring in the FSI Skills Library (baseline status: `new`).

- **Scope:** explainable valuation-review checks + cited evidence + a suggested review
  disposition. Read-only; no sign-off, no override approval, no posting, no fair-value
  determination.
- **Checks (deterministic):** fair-value-hierarchy consistency, input staleness, input
  source/traceability, IPV missing, IPV breach vs tolerance, unexplained/material
  adjustments, comparable sufficiency (market approach), Level 3 uncertainty disclosure, and
  unapproved overrides — each explainable and evidenced (see
  `scripts/calculate_or_transform.py`).
- **Controls:** R2; hard boundary against valuation sign-off, override/adjustment approval,
  posting to the GL/system of record, and fair-value determination; versioned-config
  thresholds only; independence from the desk mark; review-considerations prompts required;
  `external-delivery` approval.
- **Scripts:** `validate_input` (valuation-record schema, evaluability warnings), review
  engine, `validate_output` (evidence/citation completeness, deterministic disposition
  tie-out, sign-off/approval/posting-language screen, disclaimer, review considerations).
- **Evaluations:** trigger/routing, golden Escalate case, Level 1 market-approach edge,
  deterministic script checks, no-determination safety + injection, external-delivery
  authorization.
- **Handoffs:** downstream to `fixed-income-pricing-reviewer`, `model-validation-assistant`,
  `model-risk-documenter`, `gl-reconciler`, `audit-evidence-packager`; upstream from
  `dcf-modeler`, `three-statement-model-builder`, `merger-model-builder`, `lbo-model-builder`,
  `financials-normalizer`; governance escalation to the Valuation Control Committee and Model
  Risk Management.

### Pending before release
- Domain SME (product control / valuation control) + control-owner blind review.
- Confirm the versioned threshold/policy config source, its owner, and the IPV tolerance
  bands per asset class.
- Wire read-only MCP integrations (pricing/market-data, valuation record, policy library,
  config, document intelligence) at deployment.
