# Lending and liquidity methods and input schema

This model compares independent sources of liquidity for one household need: cash after a protected reserve, externally prepared liquidation illustrations, and loan options under explicit shocks. It does not allocate funding among options, normalize different loan sizes into a recommendation, or estimate opportunity cost, returns, interest deductibility or probabilities. Compare net funding, timing, term, balance and risks together; the lowest displayed interest cost is not a selection criterion by itself.

## Common evidence

Required envelope: `schema_version: wealth-p0-v1`, nonempty `request_id`, `household_id`, ISO `as_of`, and `engagement: {capacity: advisory|brokerage|private-bank|trust, jurisdiction: US, source_ids}`. `sources` is a nonempty registry of unique `{source_id, reference, owner, as_of, valid_until}`; each source's dates cover the review date. Identifiers are masked/opaque, not account numbers. Source claims require human verification.

`policy` requires `version`, `owner`, matching `capacity`/`jurisdiction`, current `effective_date`/`valid_until`, `source_ids`, and integer `max_quote_age_days`/`max_valuation_age_days` in 0..366. These are supplied firm assumptions, not built-in regulatory thresholds.

`upstream_issues` is required, including an explicit reviewed empty list. Rows have `artifact_id`, `code`, `message`, `status: unresolved|resolved`, `source_ids`. Resolved rows also require `resolution: {owner, reference, as_of, source_ids}`, dated no later than the request. Unresolved issues and missing citations remain findings. Top-level `unresolved_issues` must be mapped into this schema, not silently carried under the wrong name.

Every material object below requires `source_ids`; missing item citations produce needs-data. JSON numeric amounts or decimal strings are supported, never booleans/NaN/infinity. Money has at most two decimals, rates/fractions at most eight; nonnegative inputs are bounded at 1e15 unless a narrower range is stated. Null or omitted domain observations remain unknown; structural containers/enums and required policy fields reject when malformed. Lists have at most 1000 rows and unique nonempty identifiers within each list. Scripts do not parse raw agreements or fetch rates.

## Household inputs

- `currency: USD`; `horizon_months` integer 1..360.
- `funding_need: {amount, needed_by, purpose, purpose_category, source_ids}`. Amount is nonnegative money or null; date is current/future. Purpose is substantive text and category is securities-purchase/other/unknown.
- `liquid_resources: {available_cash, protected_reserve, source_ids}`. Both are money or null; available cash means currently available, unencumbered household cash. Cash alternative = max(available−reserve, 0). A reserve deficit remains a finding.
- `debt_budget: {monthly_available, basis: before-modeled-facility-service, source_ids}`. This is household cash after other expenses and debt, but before **all** service on the facility being modeled, including its existing balance. Avoid counting its current payment twice. Monthly available is money or null.
- `liquidation_options`: explicit array, possibly empty. Each `{option_id, description, gross_proceeds, fees, tax_reserve, available_date, source_ids}` is a separately prepared sale illustration. Amounts/date can be null. Net = gross−fees−supplied tax reserve; unknown tax is never zero. No sale is selected or tax calculated here. A negative net or proceeds arriving after the need becomes a finding.

## Loan options

`loan_options` is an explicit array, possibly empty; each row contains:

| Field | Meaning |
| --- | --- |
| loan_id, lender_reference, description, source_ids | Unique option and sourced terms |
| type | unsecured, property-secured or securities-backed; the last is a non-purpose SBLOC, not brokerage margin |
| draw_amount, existing_balance, credit_limit | New requested principal, existing principal on this same facility, total facility limit; money or null |
| upfront_fee, monthly_fee | Fee withheld from new draw and recurring fee paid separately; money or null. No fee financing or double-counting. |
| annual_rate_pct | Supplied current annual nominal interest rate, 0..100, or null. It is not APR. |
| rate_type | fixed or floating |
| rate_floor_pct, rate_cap_pct | Explicit percentage or null meaning no contractual floor/cap; missing keys reject. Unknown floor/cap terms must be resolved or retained as an upstream issue. |
| repayment, term_months | interest-only or amortizing; remaining term from proposed funding, integer 1..360 |
| quote_date, quote_valid_until, funding_date | Supplied ISO dates or null. Quotes cannot be future-dated, and proposed new funding cannot be historical. Quote validity must cover both the review and planned funding. |
| use_review | recorded-permitted, prohibited or unknown; recorded does not authenticate authority |
| on_demand | Explicit boolean; demand repayment remains a risk even if every modeled scenario fits |
| collateral_test | none for unsecured; origination-only or ongoing-maintenance for property-secured; ongoing-maintenance for this SBLOC model |
| maturity_funding | Supplied separate principal repayment resources for an interest-only balloon, money or null. Do not reuse protected reserves or pledged assets without sourced availability. |
| collateral | Explicit list; empty for unsecured. Secured options need the inventory below. |

Collateral rows: `{asset_id, market_value, value_reserved_elsewhere, advance_rate, eligible, valuation_date, source_ids}`. Money and advance rate may be null; advance rate is a fraction 0..1, eligibility true/false/null, valuation date nonfuture ISO or null. `value_reserved_elsewhere` is the portion of the current market value excluded from this option because it is separately encumbered; it is not another loan's debt balance. Reject duplicate asset rows; inconsistent encumbrance and stale/unknown collateral suppress the borrowing base. A source-normalized partial pledge must not count the same asset twice. Alternative options may reuse collateral only because they are not combined.

## Scenarios and arithmetic

`scenarios` is an explicit list, possibly empty, of `{scenario_id, description, rate_shock_bps, collateral_price_change_pct, advance_rate_reduction_pp, source_ids}`. The script adds a visible base case with zero shocks, so `base` is reserved. Rate shock is −10000..10000 bps; collateral price change −100..100 percent; advance-rate reduction 0..100 percentage points. The shock applies uniformly to the remaining eligible collateral, including the excluded-value portion proportionately; security-specific scenarios need a different reviewed method.

- New net proceeds = draw−withheld upfront fee. Opening total debt = existing balance+draw. These are deliberately different amounts.
- For floating debt, shocked rate = current rate+shock/100, bounded only by the explicit contractual floor/cap. Fixed rates do not change. A rate outside supported 0..100 suppresses the schedule; no zero floor is invented.
- The monthly rate is annual nominal percentage/1200. Each month, round interest to cents half-up. Interest-only loans pay interest+monthly fees, with principal balloon at term. Amortizing loans use the standard level-payment annuity on total opening debt over the stated term; zero-rate payment is principal/term. Round monthly payment to cents, cap principal repayment at balance and reconcile the last installment to zero. Fees are paid separately and never earn interest. This is a scenario convention, not a replication of a lender's actual-day, reset, holiday or rounding rules.
- Stop the monthly schedule at the earlier of maturity and horizon. Keep remaining principal, total interest, fees, principal repaid and any balloon distinct. The horizon financing cost is interest+recurring fees+upfront fee; it excludes repaid principal. Monthly budget comparison includes interest, scheduled amortization and fees. An interest-only balloon is compared separately with maturity funding, not hidden in the monthly budget. Horizon month indices are illustrative periods from the proposed funding date, not exact payment dates.
- Borrowing base = sum[(market value−reserved value) × (1+price shock/100) × max(advance rate−reduction/100,0)] across eligible collateral. Effective capacity is the lesser of that base and the credit limit. For unsecured debt it is just the limit. Unknown limit/collateral gives unknown capacity, never unlimited capacity.
- Debt over capacity = max(opening total debt−effective capacity,0). Only an ongoing-maintenance model reports this as an illustrative principal paydown. Origination-only property stress does not invent a maintenance call. No securities-sale amount or additional-collateral cure is inferred.

Dates, supplied constraints and economic gaps remain visible even when diagnostic calculations are possible. Missing or stale evidence gives needs-data; review-ready may still show a known funding gap on a cash alternative, demand risk or other disclosed tradeoff. It never means all alternatives are fundable, appropriate or legally permitted.

## Output and validation

Common draft envelope plus `result.input_snapshot`, `policy`, `upstream_issues`, `handoff_context`, household need, cash/liquidation alternatives and loan alternatives. Each loan retains terms, net new proceeds, opening total debt and every scenario's collateral capacity and monthly projection. `selected_option` is always null. Output validation reconstructs all content and findings from the bound input. A changed snapshot can generate a new self-consistent artifact; the hash is not authentication or approval.
