# Dated liability and real-asset extension

Set `extension: liability-real-assets`. Existing omitted-extension requests and evaluations remain unchanged. Use the same input/calculation/detached-output validator scripts. Common foundation fields and versioned eligible sources remain required. This extension does not accept legacy `institutional_constraints` or `candidates` fields. All rows carry an eligible `source_ref`; all assets/liabilities/scenarios/factor rows also carry a unique `id` and request `currency`.

## Contract

`policy`: `version`, `reviewed_by`, `objective`, `currency`, `effective_from`, `expires`, `discount_basis: supplied-factors-by-dated-liability`, `maximum_illiquid_fraction` in[0,1], integer `maximum_valuation_age_days`, positive `parallel_shift_bps` up to10,000. The same parallel shift magnitude defines both supplied factor perturbations.

`liability_cashflows`: nonempty unique rows with `due_date` on/after review, nonnegative `amount` and `liability_basis`. These are already projected supplied amounts; the package does not calculate benefit obligations, longevity or inflation assumptions.

`discount_factors`: exactly one row for each `liability_id`, with matching `due_date` and `policy_version`, plus positive `base_factor`, `down_factor`, `up_factor` up to10. For positive liabilities require down≥base≥up. Factors may exceed1 under a supplied negative-rate basis. No curve interpolation or assumed convention is invented.

`assets`: nonempty unique rows, `market_value`, `asset_class`, boolean `illiquid`/`real_asset`, actual `valuation_date`, `valuation_basis`, `earliest_liquidation_date`, `liquidation_fraction` in[0,1]. Real assets explicitly use real-estate/infrastructure/natural-resources. Supplied stale valuations retain issues and withhold dependent asset/coverage measures.

`opening_cash` is nonnegative unencumbered cash held separately from the listed assets; including that same cash again as an asset or cashflow is unsupported double counting. `asset_cashflows` is an explicit list, possibly empty, of unique `id`, known `asset_id`, future/current `date`, `kind: principal|distribution`, nonnegative `amount`, currency and source. Principal must not precede the asset's liquidation date; aggregate principal for an asset cannot exceed market value times liquidatable fraction. Distributions are separate projected income, not additional principal.

`scenarios`: nonempty unique rows with `policy_version`, `discount_case: base|down|up`, `liability_multiplier` in[0,10], and `asset_shocks` covering every asset exactly once. Each shock has `asset_id`, `price_return` between−1 and10, `cashflow_multiplier` in[0,10], integer `delay_days` from0 through36,500, and source. All date delays are calendar days. Projected principal cannot exceed the stressed liquidatable asset value; such a breach withholds dependent asset/cash-coverage measures.

`inventory_complete` and `inventory_source_ref` explicitly attest the supplied asset/liability/flow inventory. An incomplete inventory withholds aggregate valuation and coverage. No implied foreign-currency conversion, leverage netting, borrowed cash or repeated cash availability is supported.

## Bounded calculations

PV for each factor case = Σ(liability amount × factor). Effective duration = `(PVdown−PVup)/(2×PVbase×shift)`. Effective convexity = `(PVdown+PVup−2×PVbase)/(PVbase×shift²)`, where shift = basis points/10,000. Ratios use12-decimal rounding; cash sums and limit comparisons remain exact. Zero base PV leaves those ratios unknown.

Scenario assets = opening cash + Σ(value×(1+price return)). Apply liability multiplier to both PV and dated cash needs. Funding gap is scenario assets minus selected liability PV; funded ratio does not establish accounting funded status. Sum projected asset flows whose delayed dates fall on/before each liability date, add opening cash and subtract cumulative liabilities. Future projected inflows are not actual available balances. Compare illiquid value to total assets times the supplied limit without rounding. Report every scenario; no selection or optimization occurs.

## Sources, interpretation and engine boundary

Reviewed2026-10-04: [ASB ASOP4](https://www.actuarialstandardsboard.org/asops/asop-no-4-measuring-pension-obligations-and-determining-pension-plan-costs-or-contributions/) describes professional measurement of pension obligations and emphasizes measurement purpose and assumptions. [ASB ASOP51](https://www.actuarialstandardsboard.org/asops/assessment-disclosure-risk-associated-measuring-pension-obligations-determining-pension-plan-contributions-3/) discusses risk assessment through sensitivity/scenario methods. These references motivate explicit assumptions and specialist boundaries; this package is not an actuarial service or an assertion of standards compliance.

The institution's actuary/ALM owner supplies dated liabilities, discount factors, projection/discount basis and review evidence. Asset valuers supply actual valuation dates and liquidity assumptions. Complex curve calibration, actuarial projection, option-adjusted liabilities, stochastic inflation/longevity, derivative hedging, real-asset appraisal and ALM optimization require an approved engine with model/version/input identity, source/date/currency binding, independent benchmarks and declared limitations. The local output is an internal scenario packet; it does not certify a balance sheet or grant discretion.
