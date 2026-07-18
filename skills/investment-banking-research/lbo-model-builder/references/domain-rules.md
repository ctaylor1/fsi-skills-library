# Domain Rules — lbo-model-builder

The deterministic LBO math, the driver definitions, the scenario construction, and the
tie-outs. Formulas and defaults are **configuration** (versioned, owned by the
leveraged-finance / model-governance function), not the skill's judgment, and are never bent
to reach a desired return. Orientation: standard sponsor LBO as used in leveraged finance;
the firm's modelling standard takes precedence where it differs.

## Sources & Uses (entry, in `scripts/calculate_or_transform.py`)

```
purchase_enterprise_value = entry_ebitda * entry_multiple
transaction_fees          = transaction_fee_pct * purchase_enterprise_value
tranche_principal_j       = turns_j * entry_ebitda          # per debt tranche j
total_new_debt            = sum(tranche_principal_j)
financing_fees            = financing_fee_pct * total_new_debt
total_uses                = purchase_enterprise_value + transaction_fees + financing_fees
sponsor_equity            = total_uses - total_new_debt      # the balancing plug
total_sources             = total_new_debt + sponsor_equity
```

The acquisition is modelled cash-free / debt-free: the sponsor buys the enterprise and
overlays a new capital structure. **Sources must equal uses**; sponsor equity is the plug.
Entry leverage = `total_new_debt / entry_ebitda`.

## Operating forecast (per hold year `t`)

```
revenue_t   = revenue_{t-1} * (1 + revenue_growth)          # revenue_0 = revenue_base
ebitda_t    = revenue_t * ebitda_margin
da_t        = revenue_t * da_pct_revenue
ebit_t      = ebitda_t - da_t
capex_t     = revenue_t * capex_pct_revenue
delta_nwc_t = nwc_pct_of_revenue_change * (revenue_t - revenue_{t-1})
```

## Debt schedule and cash sweep (per year, per tranche)

Interest accrues on the **beginning-of-year** balance — this is the documented convention
that keeps the model iteration-free (no circular interest/cash reference).

```
interest_t      = sum(rate_j * beginning_balance_{j,t})
ebt_t           = ebit_t - interest_t
cash_taxes_t    = tax_rate * max(ebt_t, 0)                  # taxes floored at zero
mandatory_j,t   = min(amort_pct_j * original_principal_j, beginning_balance_{j,t})
fcf_before_sweep_t = ebitda_t - interest_t - cash_taxes_t - capex_t - delta_nwc_t
                     - sum(mandatory_j,t)
```

Optional cash sweep applies free cash flow above the minimum-cash floor to sweep-eligible
tranches in order:

```
pre_sweep_cash_t = beginning_cash_t + fcf_before_sweep_t
sweepable_cash_t = max(pre_sweep_cash_t - min_cash, 0)
sweep_budget_t   = cash_sweep_pct * sweepable_cash_t
                   (allocated to sweep-eligible tranches in order, capped at each balance)
ending_balance_{j,t} = beginning_balance_{j,t} - mandatory_j,t - sweep_{j,t}
ending_cash_t    = pre_sweep_cash_t - sum(sweep_{j,t})
net_debt_t       = sum(ending_balance_{j,t}) - ending_cash_t
```

Leverage (`net_debt_t / ebitda_t`) and interest coverage (`ebitda_t / interest_t`) are
reported each year. If `ending_cash_t < min_cash`, the year flags a liquidity shortfall
(`min_cash_ok = false`) — surfaced, not silently absorbed.

## Exit and sponsor returns

```
exit_ebitda    = ebitda_N                                   # final hold-year EBITDA
exit_enterprise_value = exit_ebitda * exit_multiple
net_debt_at_exit = net_debt_N
exit_equity_value = exit_enterprise_value - net_debt_at_exit
moic = exit_equity_value / sponsor_equity
irr  = moic^(1 / hold_years) - 1                            # single entry->exit cash flow
```

The IRR uses a single entry outflow and a single exit inflow (no interim sponsor
distributions modelled); this is deterministic and stated as such. Interim dividends /
dividend recaps are out of scope for the base engine.

## Scenarios (deterministic, documented)

Three cases are always produced. **Entry price and capital structure are fixed** across
scenarios; scenarios flex operating drivers (via additive `scenario_adjustments`, e.g. `+/-
revenue_growth`, `+/- ebitda_margin`) and the `exit_multiple`. The `base` case uses the
inputs as given. Deltas are documented, signed so that **upside improves and downside
worsens** returns. The engine and `scripts/validate_output.py` both require exit equity,
MOIC, and IRR to be **monotonic**: `downside <= base <= upside`.

## Tie-outs (every one must hold within tolerance; re-checked in validate_output)

1. `total_sources == total_uses`; `sponsor_equity == total_uses - total_new_debt`;
   `total_new_debt == sum(tranche principals)`; `purchase_ev == entry_ebitda * entry_multiple`
2. per year, per tranche: `interest == rate * beginning_balance`; sum ties to year interest
3. per year: `fcf_before_sweep == ebitda - interest - cash_taxes - capex - delta_nwc -
   mandatory_amort`
4. per year, per tranche: `ending == beginning - mandatory - sweep`; year-1 beginning ==
   S&U principal; each year's beginning == prior year's ending
5. per year: `ending_cash == beginning_cash + fcf_before_sweep - optional_sweep`
6. `exit_ev == exit_ebitda * exit_multiple`; `exit_equity == exit_ev - net_debt_at_exit`
7. `moic == exit_equity / sponsor_equity`; `(1 + irr)^hold == moic`
8. scenario values monotonic across downside / base / upside

## Assumption provenance (mandatory)

Every entry term, capital-structure term, operating driver, exit input, and liquidity input
is recorded in the `assumptions_register` with a `provenance` class and a dated `citation`.
An assumption without both is a control failure — `validate_output` rejects the pack.

## Reproducibility

`model_id = lbo-{company}-{entry_date}-{inputs_hash}`, where `inputs_hash` is a hash of the
numeric assumptions. Identical inputs reproduce the identical model and numbers.

## Hard boundaries (fail closed)

- Never output an **investment recommendation** (invest / pass / commit / allocate), a
  **guaranteed return, IRR, or MOIC**, an **investment-committee approval**, or a **fairness
  opinion** — those are licensed-human/committee outputs. The LBO is a model *conditional on
  stated assumptions*.
- Never present an **unbalanced Sources & Uses** or a debt schedule that does not roll forward.
- Never adjust a formula, tolerance, fee, leverage, or scenario delta to reach a wanted return.
- Never fabricate or leave unsourced an assumption; every number carries provenance.
- Never guarantee a return, IRR, or future exit value.
