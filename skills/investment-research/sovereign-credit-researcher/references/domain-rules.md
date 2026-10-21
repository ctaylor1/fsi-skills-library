# Nominal debt and financing method

For opening domestic debt L and foreign debt F already translated at opening FX, nominal GDP Y, depreciation e and current effective nominal rates iL/iF:

- GDP_next = Y * (1 + nominal_growth).
- FX_revaluation = F * e.
- Interest = L*iL + F*(1+e)*iF.
- Net debt creation excluding FX = interest - primary_surplus + other_cash_debt_creating_flows + other_noncash_debt_creating_flows - fiscal_cash_draw.
- Closing domestic = L + (1-new_debt_foreign_share)*net_creation; closing foreign = F*(1+e) + new_debt_foreign_share*net_creation.
- Debt-ratio change equals interest/GDP_next + FX_revaluation/GDP_next - primary_surplus/GDP_next + (other_cash_flows+other_noncash_flows)/GDP_next - fiscal_cash_draw/GDP_next - opening_debt*nominal_growth/GDP_next. The denominator is current-year GDP throughout this bridge.
- Debt-stabilizing primary surplus = interest + FX_revaluation + other_cash_flows + other_noncash_flows - fiscal_cash_draw - opening_debt*nominal_growth; divide by current GDP for the ratio convention.
- Gross financing needs = max(0, domestic_principal_due + foreign_principal_due_local*(1+e) + interest - primary_surplus + other_cash_debt_creating_flows). Compare with separately supplied committed_financing + fiscal_cash_draw. The draw reduces net debt creation and cannot exceed usable_fiscal_cash or gross needs. Preserve any gap as unresolved financing access. Supplied commitments are not authenticated market access; positive surplus is shown, not deployed or booked as debt.

Amortization affects gross financing needs, not incremental debt growth when debt is refinanced. The conditional debt path does not prove that required new issuance can occur. Positive primary balances reduce debt; a deficit is negative. Nominal growth and interest are never mixed with real rates. The foreign bucket is one composite and assumes average-year FX translation equals year-end FX translation; differing exchange paths, currency baskets, debt instrument accruals, securitizations, debt relief need a separately reviewed model. Cash and noncash stock-flow adjustments are explicitly separated: both affect debt, while noncash recognition never enters GFN. The supplied currency share allocates these non-FX debt changes; different recognition allocations require separate scenarios or a reviewed model.

External coverage is available reserves/residual-maturity short-term external debt and 12*available reserves/annual imports; missing or zero denominators yield null with an issue. Reserve availability, encumbrances, import assumptions and whole-economy debt inventory remain source judgments. These reserves are neither fiscal cash nor a promise to discharge sovereign debt. No ratio threshold assigns a rating or substitutes for IMF/World Bank framework application, institutional/political review or professional DSA acceptance.
