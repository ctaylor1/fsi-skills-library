# Changelog — financial-goal-progress-analyzer

## [0.1.0] — 2026-07-17
Initial authoring in the FSI Skills Library (baseline status: `new`).

- **Scope:** project each stated goal to its target date under approved, versioned
  assumptions; compute a funded ratio + status band (On track / At risk / Off track);
  quantify shortfall/surplus; derive illustrative planning levers. Read-only; no
  recommendation, suitability determination, advice, guarantee, trade, filing, or system
  write.
- **Projection (deterministic):** balance grown at the approved return plus a period-end
  contribution annuity, with inflation handling for `real`-terms goals; deterministic band
  mapping and lever arithmetic (see `scripts/calculate_or_transform.py` and
  `references/domain-rules.md`).
- **Controls:** R3; `required` human adjudication; hard boundary against recommendation /
  suitability / advice / guarantee / trade / filing / closure; approved versioned assumptions
  only; estimates-not-guarantees caveats.
- **Scripts:** `validate_input` (goals schema, evaluability warnings), goal-progress engine,
  `validate_output` (evidence/citation completeness, deterministic band tie-out, summary-count
  tie-out, lever presence, prohibited-decision language screen, disclaimer).
- **Evaluations:** trigger/routing, golden mixed-band case (At risk / Off track / On track +
  not-evaluable), not-evaluable edge, deterministic script checks, no-decision safety +
  injection, human-adjudication authorization.
- **Handoffs:** downstream to `suitability-reg-bi-reviewer`,
  `retirement-income-scenario-modeler`, `portfolio-rebalancing-assistant`,
  `portfolio-proposal-comparator`, `client-review-preparer`, `advisor-follow-up-assistant`,
  `senior-investor-protection-screener`.

### Pending before release
- Domain SME (planning/investment committee) + control-owner blind review; Reg BI / conduct
  review of the status-band framing.
- Confirm the approved, versioned assumptions source (returns, inflation, thresholds) and its
  owner.
- Wire read-only MCP integrations (CRM, portfolio accounting/OMS, planning engine, product
  data, approved assumptions) at deployment.
