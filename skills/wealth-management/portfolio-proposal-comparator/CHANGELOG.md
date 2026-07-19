# Changelog — portfolio-proposal-comparator

## [0.1.0] — 2026-07-17
Initial authoring in the FSI Skills Library (baseline status: `new`).

- **Scope:** even-handed, deterministic comparison of two or more portfolio proposals across
  objectives, risk/allocation, costs, taxes, liquidity, concentration, product features, and
  conflicts, with cited evidence and transparent assumptions. Read-only; no selection, no
  recommendation, no suitability determination, no trade.
- **Metrics (deterministic):** weighted expense, total cost, approved-assumption tax-drag estimate,
  allocation, single-issuer / single-sector concentration (with diversified look-through), illiquid
  weight, proprietary weight, product features (see `scripts/calculate_or_transform.py`).
- **Flags:** concentration_issuer, concentration_sector, liquidity, conflict_proprietary,
  conflict_revenue_sharing, conflict_share_class, objective_mismatch, and cross-proposal
  cost_dispersion — each cited to a source row.
- **Controls:** R3 decision-support; hard boundary against selecting/recommending a proposal, making a
  suitability/Reg BI determination, giving personalized investment/tax advice, or executing a
  trade/filing/system-of-record write; versioned-config thresholds only; `required` human adjudication.
- **Scripts:** `validate_input` (proposal/holding schema, ≥2 proposals, evaluability warnings),
  comparison engine, `validate_output` (cost tie-out, evidence/citation completeness,
  transparent-assumptions check, `adjudication_required`, no-selection-field screen,
  decision/advice-language screen, disclaimer).
- **Evaluations:** trigger/routing, golden two-proposal comparison, single-proposal edge, deterministic
  script checks, and a fail-closed safety fixture (`pack_with_recommendation.json`) that a proposal was
  selected + advice language + missing disclaimer.
- **Handoffs:** downstream to `suitability-reg-bi-reviewer`, `portfolio-rebalancing-assistant`,
  `investment-policy-statement-builder`, `financial-goal-progress-analyzer`,
  `retirement-income-scenario-modeler`, `senior-investor-protection-screener`; upstream from
  `client-review-preparer`, `advisor-follow-up-assistant`.

### Pending before release
- Domain SME (advisory & product) + control-owner blind review; conflicts/fairness review of the flag
  set and even-handedness of the presentation.
- Confirm the versioned threshold/tax-assumption config source and its owner.
- Wire read-only MCP integrations (OMS/portfolio-accounting, product data, planning engine, CRM,
  disclosures/restrictions, config) at deployment.
