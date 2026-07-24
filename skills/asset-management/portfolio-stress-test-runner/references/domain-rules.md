# Domain Rules - portfolio-stress-test-runner

The deterministic stress-test math, the position-factor revaluation, the driver attribution,
the reconciliation, and the tie-outs. Formulas, tolerance, and conventions are
**configuration** (versioned, owned by the risk / model-governance function), not the
skill's judgment, and are never bent to reach a desired loss. Scenarios are **inputs**
consumed from an approved source; the runner applies them, it does not author them.
Orientation: standard first-order factor-based stress revaluation as used in market/portfolio
risk; the firm's approved stress methodology takes precedence where it differs.

## Position-factor revaluation (per position `i`, per factor `f`, in `scripts/calculate_or_transform.py`)

Each position carries an approved **sensitivity** to each risk factor (P&L per unit factor
shock, in currency) and an optional **convexity** (second-order term):

```
contribution(i, f) = sensitivity(i, f) * shock(f) + 0.5 * convexity(i, f) * shock(f)**2
position_pnl(i)    = sum over f of contribution(i, f)
scenario_pnl       = sum over i of position_pnl(i)
stressed_value     = portfolio_base_value + scenario_pnl
pnl_pct            = scenario_pnl / portfolio_base_value
```

The same `contribution(i, f)` values feed **both** attributions, so the position walk and the
factor walk always reconcile to the identical `scenario_pnl`. Sensitivities are approved
model outputs (e.g. `beta * market_value` for an equity factor, `-modified_duration *
market_value` for a rate factor, `-spread_duration * market_value` for a credit-spread
factor); the runner consumes them, it does not derive or re-estimate them.

## Shocks (consumed, never invented)

A scenario is a set of `{factor_id -> shock}` pairs plus provenance. Shock units are defined
by the approved risk-factor model (e.g. relative return for equity factors, absolute decimal
change for rate/spread factors) and must be consistent with the sensitivity units. The runner
**never authors, edits, extends, or improvises a shock or a scenario** - see Hard boundaries.

## Driver attribution

- **By position**: `position_pnl(i)` for each position, ordered by P&L ascending (largest
  loss first) then `position_id` for stable ties; each row also lists its per-factor
  `factor_contributions`.
- **By factor**: `factor_pnl(f) = sum over i of contribution(i, f)`, ordered by absolute P&L
  descending then `factor_id`.

Ordering is presentation only and deterministic; it implies no recommendation.

## Reconciliation to the approved engine

When the input supplies `approved_engine_totals[scenario_id]` (the firm's official stress
engine result), the run records, per scenario, `{approved_engine_total, computed_total,
difference, within_tolerance}`. A difference beyond the configured tolerance is a **break**:
`validate_output` fails closed rather than presenting a run that silently disagrees with the
system of record.

## Tie-outs (every one must hold within tolerance; re-checked independently in validate_output)

1. `sum(position_pnl) == scenario_pnl`
2. `sum(factor_pnl) == scenario_pnl`
3. `position_pnl(i) == sum over f of contribution(i, f)` for every position
4. `stressed_value == portfolio_base_value + scenario_pnl`
5. reconciliation (when an approved-engine total is supplied): `|computed_total -
   approved_engine_total| <= tolerance`

## Assumption provenance (mandatory)

Every scenario, position, and factor sensitivity is recorded in the `assumptions_register`
with a `provenance` class and a dated `citation`; scenario-definition entries additionally
carry `approved: true`. An assumption without provenance/citation, or a scenario not marked
approved, is a control failure - `validate_output` rejects the run.

## Version / effective-date rules

- `as_of` (portfolio + sensitivities) and `run_date` (execution) are both recorded.
- `scenario_set_version`, `model_version`, and `config_version` are versioned contracts; a
  change is a new version, never an in-place edit, so a run is reproducible and auditable.
- The run is invalid if it mixes a scenario set with a portfolio `as_of` it was not approved
  against without recording the mismatch.

## Reproducibility & durable run IDs

`run_id = stressrun-{portfolio_id}-{as_of}-{inputs_hash}`, where `inputs_hash` is a SHA-256
over the numeric positions/sensitivities, the approved scenario shocks and set versions, the
approved-engine totals, and the model/config versions. Identical inputs reproduce the
identical `run_id` and the identical numbers; changing any assumption changes the hash, so
the audit trail shows exactly what moved.

## Hard boundaries (fail closed)

- **Never invent, design, edit, extend, or improvise a scenario or a shock.** Scenarios are
  consumed from an approved source (`stress-test-scenario-designer` or an approved scenario
  library) and must be `approved: true` with a `scenario_set_id`. `validate_input` and
  `validate_output` both reject anything else. Scenario **design** is the job of
  `stress-test-scenario-designer`.
- **Never issue an investment recommendation or action instruction** - no buy/sell/hold, no
  hedge/rebalance/de-risk/trim/rotate/exit instruction, no allocation advice, no "the loss
  implies you should ...". The run computes and attributes losses; the action decision is a
  licensed-human/committee judgment.
- **Never set or change a risk limit, mandate an action on a breach, or make a capital
  determination.** Comparing losses to limits and escalating is `market-risk-limit-monitor`.
- **Never present a run that fails a tie-out or breaks reconciliation** with the approved
  engine.
- **Never fabricate or leave unsourced** a position, sensitivity, or scenario; every input
  carries provenance, and every scenario carries approval.
- **Never bend a formula, tolerance, rounding, or attribution rule** to reach a wanted loss.
