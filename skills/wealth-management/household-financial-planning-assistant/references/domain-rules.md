# Calculation rules and invariants

1. Available pool = balance minus reserved amount. Sum assignments across all goals once per pool.
   If assignments exceed available money, flag `shared-pool-overallocated`; affected projections
   are not evaluable. Duplicate account IDs across pools are structural errors.
2. Monthly debt service uses supplied minimum plus additional payment, capped at the current
   balance plus one month's rounded interest. Monthly surplus before goals = after-tax income
   minus non-debt living expenses minus debt service minus reserve contribution. Subtract the sum
   of declared goal contributions once to obtain the remainder. Negative remainder is a funding
   conflict, not permission to reduce goals or refinance debt automatically.
3. Debt projection uses fixed nominal APR/12, cent-rounded monthly interest and month-end
   payments. Payment <= first month's interest cannot reduce principal. Report it without claiming
   a payoff date. Limit payoff search to 1200 months. Fees, variable rates, penalties, new charges
   and income changes are excluded; no avalanche/snowball recommendation is inferred.
4. Whole months are the calendar month difference minus one when target day precedes as-of day.
   Goal projection: `FV = B*(1+r)^n + C*((1+r)^n-1)/r`, `r = nominal annual return/12`.
   For zero r, use `B + C*n`. Contributions occur at month end and all figures use one currency.
5. A real target at any modeled month n is `real_target * (1+annual_inflation)^(n/12)`.
   Recompute that target for EVERY extension month. Never freeze inflation at the original date.
   The first passing month is returned within the supplied extension search limit. The additional
   contribution lever solves the ordinary annuity at the original target date; round its display
   to cents. It is an illustration, not a new commitment or simultaneous solution for all goals.
6. Funded ratio = projected nominal value / nominal target at date. `on-track` >=1, `at-risk`
   >= supplied at-risk ratio, otherwise `off-track`. These bands describe conditional projections,
   not household affordability, suitability or probability. No default assumptions are supplied.

Inputs and final monetary displays use cents; rates and ratios retain precision. Tests include an
independently checked 239-month real target needing 36 extra months, not the old 21-month
extension with frozen inflation. Structural checks and reconstructed output do not authenticate
financial assumptions or replace professional judgment.
