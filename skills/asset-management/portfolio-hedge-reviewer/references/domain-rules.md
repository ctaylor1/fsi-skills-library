# Domain Rules — portfolio-hedge-reviewer

The deterministic exposure/sensitivity math, the factor conventions, the coverage and
scenario definitions, and the tie-outs. Formulas, factor-unit definitions, and tolerances
are **configuration** (versioned, owned by the model-governance / market-risk function), not
the skill's judgment, and are never bent to reach a desired coverage or P&L. Orientation:
standard first-order (linear) sensitivity/scenario analysis as used in buy-side portfolio
risk; the firm's approved model standard takes precedence where it differs.

## Sensitivity convention

Each sensitivity `value` is the P&L, in the packet's **reporting units**, for a **+1 shock of
the factor's standardized unit** (declared in `risk_factors[f].unit`, e.g. `+1bp` for rates,
`+1pct` for equity). This is how an approved risk engine stores first-order sensitivities
(DV01-style for rates, dollar-delta for equity, CS01 for credit, FX delta). Scenario shocks
are expressed in the **same** standardized factor units, so scenario P&L is a linear sum.

## Exposure, residual, and coverage (in `scripts/calculate_or_transform.py`)

For portfolio sensitivities `P[f]`, a candidate hedge's sensitivities `H[f]`, over the
declared factor set:

```
residual[f]        = P[f] + H[f]                       # per factor, after the hedge
gross_portfolio    = sum_f |P[f]|                       # gross first-order exposure
residual_gross     = sum_f |residual[f]|
coverage_overall   = (gross_portfolio - residual_gross) / gross_portfolio
coverage[f]        = (|P[f]| - |residual[f]|) / |P[f]|  # per factor, when P[f] != 0
```

Coverage is a **sensitivity-offset** measure only. A hedge that touches a factor the
portfolio has no exposure to **adds** exposure (residual = hedge sensitivity); this is a
documented result surfaced to the analyst, not a control failure.

## Scenario P&L

For a scenario with shocks `k[f]` (standardized factor units):

```
portfolio_scenario_pnl = sum_f P[f]        * k[f]
hedge_scenario_pnl     = sum_f H[f]        * k[f]
hedged_scenario_pnl    = sum_f residual[f] * k[f]  ==  portfolio_scenario_pnl + hedge_scenario_pnl
```

The identity on the right (linearity) is a tie-out, re-checked in `validate_output`. Scenario
P&L is a **first-order estimate**, not a full revaluation.

## Cost

A supplied hedge `cost` (premium, carry, etc.) is **carried through as-is** and tabulated
next to coverage and scenario P&L. This skill does **not** estimate transaction cost, market
impact, or cost-effectiveness — route those to `transaction-cost-estimator`.

## Reconciliation to approved-engine totals

When `portfolio.approved_engine_totals` are supplied, the engine reconciles:

```
computed gross_portfolio      ==  approved gross_sensitivity        (within reconcile tol)
computed portfolio_scenario_pnl[s] == approved scenarios[s]         (within reconcile tol)
```

Reconcile tolerance is `max(RECON_ABS, RECON_REL * |approved|)`. A break fails closed in
`validate_output`; the packet is not presented as tied out until it reconciles or the break
is explained by a human.

## Tie-outs (every one must hold within tolerance; re-checked in validate_output)

1. `residual[f] == P[f] + H[f]` for every factor and every hedge
2. `residual_gross == sum_f |residual[f]|`
3. `coverage_overall == (gross_portfolio - residual_gross) / gross_portfolio`
4. `portfolio_scenario_pnl[s] == sum_f P[f]*k[f]`; `hedge_scenario_pnl[s] == sum_f H[f]*k[f]`
5. `hedged_scenario_pnl[s] == portfolio + hedge == sum_f residual[f]*k[f]` (linearity)
6. reconciliation to approved-engine totals (when supplied)

## Assumption provenance (mandatory)

Every model reference, factor-unit definition, portfolio sensitivity, hedge sensitivity,
hedge cost, and scenario shock is recorded in the `assumptions_register` with a `provenance`
class and a dated `citation`. An assumption without both is a control failure —
`validate_output` rejects the packet.

## Reproducibility & durable identifiers

`packet_id = hedge-{case_id}-{valuation_date}-{inputs_hash}`, where `inputs_hash` is a hash
of the numeric assumptions (model, factors, sensitivities, hedges, scenarios). Identical
inputs reproduce the identical packet and numbers. `case_id` is the durable case/job ID that
travels with the packet into every downstream handoff.

## Hard boundaries (fail closed)

- Never **select, recommend, rank, score-to-a-winner, or endorse** a hedge, and never imply
  one is best/optimal/preferred — hedge choice is a portfolio-manager / investment-committee
  judgment. The comparison table is neutral: it presents figures, not a pick.
- Never **decide whether to hedge**, size a hedge, or set a hedge ratio target.
- Never **authorize, stage, route, or execute** a trade or overlay.
- Never provide **personalized investment, legal, or tax advice**, or **guarantee** hedge
  efficacy, protection, or a return.
- Never **invent** a hedge, scenario, sensitivity, or cost; every number carries provenance.
- Never adjust a formula, tolerance, factor unit, or scenario shock to reach a wanted
  coverage or P&L.
- Never present an **unreconciled** packet (approved-engine break) as tied out.


## Phase 4 supplied full-repricing extension

For explicitly selected `advanced-derivatives`, use [the separate advanced contract](advanced-derivatives.md). Preserve full-book engine/benchmark binding and the no-fallback boundary; the first-order method above is not a complex derivative pricer.
