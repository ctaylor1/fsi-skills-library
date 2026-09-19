# Changelog — retirement-income-scenario-modeler

## [0.2.0] — 2026-09-16

Independent review correction: require and preserve the upstream issue inventory with origin/status/citations; unresolved concerns remain findings, and external resolution requires cited dated evidence. Added executed carry-forward regressions.

Rebuilt for Wave 7 wealth management P1 with the shared `wealth-p0-v1` evidence envelope,
versioned/cited assumptions, full input-bound reconstruction, explicit unknowns and substantive
planning outputs. Preserves the distinct workflow job and draft-only human-review boundary.

Replaced ambiguous depletion flag with separate shortfall/depletion measures, annual cent-level reconciliations and complete assumption snapshots. Explicit current-date start, benefit COLA timing, effective-tax proxies and model exclusions replace implicit assumptions. The 0.1 schema is intentionally replaced.

Executed domain/arithmetic regressions and contract tests accompany the package. SME/compliance review, source authentication, deployment connectors and real-agent acceptance remain separate release work. Historical notes below describe prior behavior and are not the current contract.

## Historical package notes

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
