# Changelog — portfolio-risk-diversification-check

## [0.1.0] — 2026-07-17
Initial authoring in the FSI Skills Library (baseline status: `existing-updated` relative to
the AWS baseline — stronger evidence, transparent methods, and a no-personalized-advice
guardrail).

- **Scope:** explainable diversification/concentration checks + cited evidence + a descriptive
  diversification band. Read-only; no advice, no recommendation, no forecast, no trade.
- **Checks (deterministic):** single-name, top-N, sector, geography, asset-class, factor tilt,
  correlation, and liquidity concentration — each explainable and evidenced, plus summary
  metrics (HHI, effective holdings, top-N weight) (see `scripts/calculate_or_transform.py`).
- **Controls:** R2; hard boundary against personalized investment advice, suitability/"good
  investment" judgments, buy/sell/hold/rebalance recommendations, and return/price forecasts;
  versioned-config thresholds only; educational prompts required; `external-delivery` approval.
- **Scripts:** `validate_input` (holdings schema, evaluability warnings), the check engine,
  `validate_output` (evidence/citation completeness, deterministic band tie-out,
  advice-language screen, disclaimer, educational prompts).
- **Evaluations:** trigger/routing, golden Highly-concentrated case, single-holding edge,
  deterministic script checks, no-advice safety + injection, external-delivery authorization.
- **Handoffs:** downstream to `portfolio-holdings-summarizer`,
  `prospectus-plain-language-breakdown`, `trade-confirmation-explainer`,
  `corporate-action-interpreter`, `margin-collateral-optimizer`, and a licensed human for any
  advice/suitability/trade question.

### Pending before release
- Domain SME (risk/portfolio analytics) + control-owner blind review; compliance review of the
  no-advice boundary and disclaimer wording.
- Confirm the versioned threshold/band config source and its owner.
- Wire read-only MCP integrations (positions/custody, market & reference data — classification,
  factor, correlation, liquidity — and config) at deployment.
