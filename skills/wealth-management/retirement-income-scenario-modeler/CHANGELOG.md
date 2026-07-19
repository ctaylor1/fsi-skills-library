# Changelog — retirement-income-scenario-modeler

## [0.1.0] — 2026-07-18
Initial authoring in the FSI Skills Library (baseline status: `new`).

- **Scope:** deterministic retirement-income decumulation model — spending, inflation,
  guaranteed income, approved taxes, a documented withdrawal order, base / favorable / adverse
  scenarios with sequence-of-returns and longevity risk, shortfall/depletion behavior, and
  model checks — as a **range** draft for human review.
- **Controls:** R3 decision support; no recommendation/guarantee/decision; results as a range;
  assumptions carry provenance; NPI/PII handling; `required` licensed-advisor + client
  adjudication before any recommendation, decision, trade, or system-of-record write.
- **Scripts:** `validate_input`, `calculate_or_transform` (deterministic decumulation engine),
  `validate_output` (formula tie-outs, funding/tax identities, scenario monotonicity,
  provenance, advice/guarantee/decision screen, disclaimer).
- **Evaluations:** trigger/routing, golden three-scenario model, deterministic script checks,
  fail-closed safety on a non-compliant pack, injection refusal, decision-adjudication
  authorization.
- **Handoffs:** upstream `financial-goal-progress-analyzer`, `investment-policy-statement-builder`,
  `portfolio-proposal-comparator`; downstream `suitability-reg-bi-reviewer`,
  `client-review-preparer`, `advisor-follow-up-assistant`, `portfolio-rebalancing-assistant`.

### Fixed (pre-release)
- **Tie-out self-checks were vacuous.** `calculate_or_transform` compared each rounded
  quantity to the very expression that produced it, so every per-scenario tie-out (and
  `model_checks.all_tieouts_ok`) was always true regardless of correctness. The engine now
  **independently re-derives** each tie-out from the emitted rows (the same computation
  `validate_output` performs), so the flags reflect a real check. `validate_output` now also
  **fails closed when a pack self-reports a tie-out failure** (`all_tieouts_ok` false, or any
  scenario `tieouts.*_ok` false), proven by `evals/files/retirement_pack_selfreport_tieout_fail.json`
  (`safety-selfreported-tieout-fail`, `expect_exit 1`).

### Pending before release
- Domain SME (retirement planning) blind review; capital-market and tax assumption-set review.
- Model-risk-management review of the decumulation methodology and scenario construction.
- Wire read-only portfolio-accounting / planning-engine / config MCP integrations at deployment.
