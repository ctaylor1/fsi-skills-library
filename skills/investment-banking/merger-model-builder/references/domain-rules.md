# Domain Rules — merger-model-builder

Every formula the pro forma engine applies. All figures are mechanical consequences of the
documented drivers; nothing here is a valuation, fairness, or investment view. Dollar figures
may be in millions and shares in millions — ratios are unit-consistent. Tax factor
`atf = 1 - pro_forma_tax_rate`.

## Consideration & financing

| Quantity | Formula |
| -------- | ------- |
| Base premium | `offer_price / target_price - 1` (or `premium_pct` if the offer price is not given) |
| Offer price (scenario) | `target_price * (1 + base_premium * premium_mult)` |
| Offer value (equity purchase price) | `offer_price * target_shares_diluted` |
| Cash consideration | `offer_value * cash_pct` |
| Stock consideration | `offer_value * stock_pct` (with `cash_pct + stock_pct = 1`) |
| New shares issued | `stock_consideration / acquirer_share_price` |
| New debt | `max(cash_consideration - cash_on_hand_used, 0)` |
| Incremental interest | `new_debt * new_debt_rate` |
| Foregone interest | `cash_on_hand_used * cash_yield_foregone` |

## After-tax pro forma adjustments

| Adjustment | Pre-tax | Tax treatment |
| ---------- | ------- | ------------- |
| Synergies | `run_rate_pretax * phasing_pct * synergy_realization` | `* atf` |
| Incremental interest | `new_debt * new_debt_rate` | `* atf` (subtract) |
| Foregone interest | `cash_on_hand_used * cash_yield_foregone` | `* atf` (subtract) |
| Intangible amortization | `intangible_writeup / intangible_amort_years` | `* atf` **only if `amort_tax_deductible`**, else full (subtract) |
| Financing-fee amortization | `financing_fees / financing_fee_amort_years` | `* atf` (subtract) |
| Transaction fees | one-time | **excluded** from run-rate EPS (affect goodwill/equity, not recurring accretion) |

## EPS, accretion, ownership

| Quantity | Formula |
| -------- | ------- |
| Acquirer standalone EPS | `acquirer_net_income / acquirer_shares_diluted` |
| Pro forma net income | `acquirer_NI + target_NI + synergies_at - interest_at - foregone_at - amort_at - ffee_at` |
| Pro forma shares | `acquirer_shares_diluted + new_shares_issued` (target's own shares are **not** carried over) |
| Pro forma EPS | `pro_forma_net_income / pro_forma_shares` |
| Accretion/(dilution) $ | `pro_forma_eps - standalone_eps` |
| Accretion/(dilution) % | `accretion_dollar / standalone_eps * 100` |
| Verdict | `accretive` if % > 0.1, `dilutive` if % < -0.1, else `neutral` |
| Acquirer ownership % | `acquirer_shares_diluted / pro_forma_shares * 100` |
| Target ownership % | `new_shares_issued / pro_forma_shares * 100` (sums to 100%) |

## Breakeven synergies

Pre-tax run-rate synergies that make base-case accretion exactly zero, holding all other
base-case drivers fixed:

```
required_pf_ni     = standalone_eps * pro_forma_shares
non_synergy_ni     = acquirer_NI + target_NI - interest_at - foregone_at - amort_at - ffee_at
synergies_needed_at = required_pf_ni - non_synergy_ni
breakeven_pretax   = synergies_needed_at / atf
```

A **negative** breakeven means the deal is accretive even with zero synergies (you would need
to destroy value to reach neutral).

## Scenarios (deterministic)

Each scenario applies a `synergy_realization` and a `premium_mult` to the base drivers.
Defaults (overridable): base `(1.0, 1.0)`, upside `(1.2, 0.9)`, downside `(0.6, 1.15)`.
Because more synergy and a lower premium are each more accretive, accretion is **monotonic**:
`downside <= base <= upside`. `validate_output` enforces this.

## Sensitivity grid (deterministic)

A 2-D grid of accretion % with rows = premium multiplier `[0.8, 1.0, 1.2]` and cols = synergy
realization `[0.5, 1.0, 1.5]`, each cell a full recompute.

## Hard boundaries (fail closed)

- Never state or imply a **recommendation to transact**, a **buy/sell/hold** view, a **price
  target**, or a **valuation/fairness opinion**. Report the mechanical pro forma only.
- Never **tune drivers to force a verdict**; drivers are sourced and versioned.
- Never carry the **target's own share count** into pro forma shares.
- Always **tax-effect consistently** and **exclude one-time transaction fees** from run-rate
  EPS.
