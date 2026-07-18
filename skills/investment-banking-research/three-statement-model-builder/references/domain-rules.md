# Domain Rules — three-statement-model-builder

The deterministic model math, driver definitions, scenario construction, and tie-outs.
Formulas, default deltas, and tolerance are **configuration** (versioned, owned by the
valuation / model-governance function), not the skill's judgment, and are never bent to reach
a desired output. Orientation: a standard integrated three-statement model as used in
banking / equity research; the firm's modelling standard takes precedence where it differs.

## Drivers (14, each `{value, source}`; see `scripts/validate_input.py`)

`revenue_growth`, `gross_margin`, `opex_pct_revenue`, `depreciation_rate`,
`capex_pct_revenue`, `dso`, `dio`, `dpo`, `other_current_assets_pct_revenue`,
`other_current_liabilities_pct_revenue`, `tax_rate`, `interest_rate`, `debt_repayment`,
`dividend_payout_ratio`.

## Income statement (per forecast year `t`, in `scripts/calculate_or_transform.py`)

```
revenue_t      = revenue_{t-1} * (1 + revenue_growth)
gross_profit_t = revenue_t * gross_margin
cogs_t         = revenue_t - gross_profit_t
opex_t         = revenue_t * opex_pct_revenue
ebitda_t       = gross_profit_t - opex_t
depreciation_t = depreciation_rate * ppe_net_{t-1}     # on OPENING net PP&E
ebit_t         = ebitda_t - depreciation_t
interest_t     = interest_rate * debt_{t-1}            # on OPENING debt -> no circularity
pretax_t       = ebit_t - interest_t
tax_t          = max(0, pretax_t) * tax_rate           # no tax benefit modelled on losses
net_income_t   = pretax_t - tax_t
```

## Balance sheet (driven items)

```
accounts_receivable_t = revenue_t / 365 * dso
inventory_t           = cogs_t / 365 * dio
other_current_assets_t = revenue_t * other_current_assets_pct_revenue
capex_t               = revenue_t * capex_pct_revenue
ppe_net_t             = ppe_net_{t-1} + capex_t - depreciation_t
accounts_payable_t    = cogs_t / 365 * dpo
other_current_liab_t  = revenue_t * other_current_liabilities_pct_revenue
debt_t                = max(0, debt_{t-1} - debt_repayment)   # scheduled amortization, floored
dividends_t           = dividend_payout_ratio * max(0, net_income_t)
equity_t              = equity_{t-1} + net_income_t - dividends_t
```

`other_assets` and `other_liabilities` are held flat from the base year unless separately
driven. `cash` is **not** driven directly — it is the cash-flow plug (below).

## Cash-flow statement (indirect method)

```
CFO_t = net_income_t + depreciation_t
        - Δaccounts_receivable - Δinventory - Δother_current_assets
        + Δaccounts_payable + Δother_current_liabilities
CFI_t = - capex_t
CFF_t = - actual_repayment_t - dividends_t     # actual_repayment = debt_{t-1} - debt_t
net_change_in_cash_t = CFO_t + CFI_t + CFF_t
cash_t = cash_{t-1} + net_change_in_cash_t
```

## Why the balance sheet balances (by construction)

With `Δ` the year-over-year change and `other_assets`/`other_liabilities` flat:

```
ΔAssets   = Δcash + ΔAR + Δinv + ΔOCA + Δppe
Δcash     = CFO + CFI + CFF
Δppe      = capex - depreciation
=> ΔAssets = net_income + ΔAP + ΔOCL - actual_repayment - dividends
ΔLiab+Eq  = ΔAP + ΔOCL + Δdebt + Δequity
          = ΔAP + ΔOCL - actual_repayment + (net_income - dividends)
=> ΔAssets - ΔLiab+Eq = 0
```

So if the **base year balances**, every forecast year balances. Interest and depreciation are
both computed on **opening** balances, so there is no interest↔cash circular reference and the
model is fully reproducible. A base year that does **not** tie is surfaced (input warning) and
carried through honestly — never silently plugged — so `validate_output` fails closed on the
identity.

## Scenarios (deterministic, documented)

Three cases are always produced. `base` uses the drivers as given. `upside` and `downside`
apply additive deltas to `revenue_growth` and `gross_margin` from `doc.scenarios` (default:
`upside +0.03 / +0.02`, `downside -0.03 / -0.02`), signed so that **upside improves and
downside worsens** the forecast. `scripts/validate_output.py` requires final-year revenue to
be **monotone**: `upside >= base >= downside`.

## Tie-outs (every one must hold within tolerance; re-checked in validate_output)

1. **Balance-sheet identity** every year: `total_assets == total_liabilities + equity`.
2. **Cash tie** every year: cash-flow `ending_cash == balance_sheet cash`.
3. **Equity roll-forward**: `equity_t == equity_{t-1} + net_income_t - dividends_t`.
4. **PP&E roll-forward**: `ppe_net_t == ppe_net_{t-1} + capex_t - depreciation_t`.
5. **Scenario monotonicity**: final-year revenue `upside >= base >= downside`.

Tolerance is `0.01` in model units. `validate_output` re-derives each check from the stored
statements rather than trusting the model's own `checks` block.

## Assumption provenance (mandatory)

Every driver carries a `source`. An assumption without a source, or a missing required
driver, is a control failure — `validate_output` rejects the model.

## Reproducibility

`model_id = 3sm-{company-slug}-{as_of}-0001`; `inputs_hash` is a 16-char SHA-256 of the
canonical input. Identical inputs reproduce identical numbers.

## Hard boundaries (fail closed)

- Never output an **investment recommendation** (buy / sell / hold / over- or under-weight),
  a **price target**, a **fair-value conclusion presented as a decision**, or a **fairness
  opinion** — those are licensed-human / committee outputs.
- Never **discount the model to a value** — that is `dcf-modeler`'s scope; the value judgment
  is a human's.
- Never present the forecast as a **guarantee** or a **forecast of actual results**.
- Never **bend a formula, tolerance, or scenario delta** to reach a wanted output.
- Never **fabricate or leave unsourced** a driver; every assumption carries a source.
- Never **silently plug** a base-year imbalance; surface it and fail closed on output.
