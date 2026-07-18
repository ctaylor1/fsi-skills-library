# Changelog — fixed-income-pricing-reviewer

## [0.1.0] — 2026-07-17
Initial authoring in the FSI Skills Library (baseline status: `new`).

- **Scope:** explainable fixed-income pricing-exception checks + cited evidence + suggested
  review priority (per instrument and overall). Read-only; no valuation determination, no price
  approval/override/booking, no IPV sign-off.
- **Checks (deterministic):** `mark_vs_independent`, `spread_to_comparables`,
  `price_movement_unexplained`, `stale_price` (escalator), `liquidity_adj_plausibility`,
  `fair_value_level_inconsistent` (escalator), `comparable_support_thin` — each explainable and
  evidenced, with missing-input checks reported `not_evaluable` (see
  `scripts/calculate_or_transform.py`).
- **Controls:** R2; hard boundary against valuation determination, price
  approval/override/restatement/booking, IPV sign-off, exception waiver, and conduct/intent
  assertions; versioned-config tolerances only; benign-explanation prompts required;
  `external-delivery` approval.
- **Scripts:** `validate_input` (marks schema, evaluability warnings), pricing-check engine,
  `validate_output` (evidence/citation completeness, deterministic per-instrument + overall
  priority tie-out, determination/approval/mark-action language screen, disclaimer, benign
  prompts).
- **Evaluations:** trigger/routing, golden Elevated case (2 focal instruments), invalid-input
  and no-independent-price edges, deterministic script checks, no-determination safety +
  injection, external-delivery authorization.
- **Handoffs:** downstream to `valuation-reviewer`, `model-validation-assistant`,
  `surveillance-alert-triager`, `market-surveillance-alert-investigator`,
  `communications-compliance-reviewer`, `trade-confirmation-explainer`; price challenge / override
  / IPV sign-off / booking reserved for the human valuation-control function.

### Pending before release
- Domain SME (valuation control / IPV) + control-owner blind review; conduct-language review.
- Confirm the versioned threshold/liquidity-band/priority config source and its owner.
- Wire read-only MCP integrations (IPV/independent-pricing, market & reference data, OMS/EMS
  marks, config) at deployment.
