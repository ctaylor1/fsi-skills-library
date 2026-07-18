# Domain Rules — dcf-modeler

The deterministic DCF math, the driver definitions, the scenario construction, and the
tie-outs. Formulas and defaults are **configuration** (versioned, owned by the valuation /
model-governance function), not the skill's judgment, and are never bent to reach a desired
answer. Orientation: standard unlevered-FCF DCF as used in banking/equity research; the
firm's valuation standard takes precedence where it differs.

## Free-cash-flow build (per forecast year `t`, in `scripts/calculate_or_transform.py`)

```
revenue_t   = revenue_{t-1} * (1 + revenue_growth_t)
ebit_t      = revenue_t * ebit_margin_t
nopat_t     = ebit_t * (1 - tax_rate)
da_t        = revenue_t * da_pct_revenue
capex_t     = revenue_t * capex_pct_revenue
delta_nwc_t = nwc_pct_of_revenue_change * (revenue_t - revenue_{t-1})
ufcf_t      = nopat_t + da_t - capex_t - delta_nwc_t          # unlevered free cash flow
```

## Discount rate (WACC)

Computed from stated components (or an explicit `wacc.override`):

```
cost_of_equity        = risk_free + beta * equity_risk_premium        # CAPM
after_tax_cost_of_debt = cost_of_debt_pretax * (1 - tax_rate)
WACC = weight_equity * cost_of_equity + weight_debt * after_tax_cost_of_debt
```

Weights should sum to 1 (input validation warns otherwise). WACC is held constant across
scenarios; scenarios flex operating drivers, not the discount rate, unless the input
overrides it.

## Discounting convention

- `end_year` (default): discount factor for year `t` is `1 / (1 + WACC)^t`.
- `mid_year`: `1 / (1 + WACC)^(t - 0.5)` — assumes cash flows arrive mid-period.
- Terminal value is discounted with the **final forecast year's** discount factor.

## Terminal value

| Method | Formula | Guard |
| ------ | ------- | ----- |
| `gordon` | `TV = UFCF_n * (1 + g) / (WACC - g)` | **WACC must exceed g**; otherwise the value is invalid and the model fails closed. |
| `exit_multiple` | `TV = exit_multiple * EBITDA_n`, where `EBITDA_n = EBIT_n + D&A_n` | Multiple must be a comparable, sourced figure. |

## Enterprise-to-equity bridge (explicit, auditable)

```
equity_value = enterprise_value
             - total_debt
             + cash_and_equivalents
             - minority_interest
             - preferred_equity
             + investments_in_associates
value_per_share = equity_value / shares_outstanding
```

Each line is emitted as a signed bridge item so the walk is inspectable.

## Scenarios (deterministic, documented)

Three cases are always produced. The `base` case uses the input drivers as given; `upside`
and `downside` apply the additive deltas in `scenario_adjustments` (e.g. `+/- growth`,
`+/- margin`). Deltas are documented, symmetric where sensible, and signed so that
**upside improves and downside worsens** free cash flow. The engine and
`scripts/validate_output.py` both require enterprise, equity, and per-share values to be
**monotonic**: `downside <= base <= upside`.

## Tie-outs (every one must hold within tolerance; re-checked in validate_output)

1. `enterprise_value == sum(PV of UFCF) + PV(terminal value)`
2. `PV of UFCF_t == UFCF_t * discount_factor_t` for every year
3. discount factors are non-increasing across the forecast
4. `equity_value == enterprise_value + sum(bridge adjustments)`
5. `value_per_share * shares_outstanding == equity_value`
6. scenario values monotonic across downside / base / upside

## Assumption provenance (mandatory)

Every driver, WACC component, terminal input, and bridge item is recorded in the
`assumptions_register` with a `provenance` class and a dated `citation`. An assumption
without both is a control failure — `validate_output` rejects the pack.

## Reproducibility

`model_id = dcf-{company}-{valuation_date}-{inputs_hash}`, where `inputs_hash` is a hash of
the numeric assumptions. Identical inputs reproduce the identical model and numbers.

## Hard boundaries (fail closed)

- Never output an **investment recommendation** (buy / sell / hold / over- or
  under-weight), a **price target**, a **fair-value conclusion presented as a decision**, or
  a **fairness opinion** — those are licensed-human/committee outputs. The DCF is a model
  *conditional on stated assumptions*.
- Never present a Gordon terminal value when `WACC <= g`.
- Never adjust a formula, tolerance, or scenario delta to reach a wanted valuation.
- Never fabricate or leave unsourced an assumption; every number carries provenance.
- Never guarantee a return, upside, or future price.
