# Annual calculation and reconciliation

The first row starts at `as_of` with current opening balances. Each row represents a complete
annual planning interval, not a prorated tax year. Ages run start through end inclusive.
No saving or return between a current age and a later retirement age is silently assumed.

1. Spending at year j is first-year net spending times `(1 + combined inflation)^j`, cent-rounded.
   A supplied income is active at its start through end ages. Gross benefit at age a is its
   first-payment amount times `(1 + COLA)^(a - income.start_age)`. Income tax is gross times its
   supplied effective proxy, rounded to cents; net = gross minus tax.
2. Spending-gap strategy draws only the remaining net need. Gross amount is remaining need
   divided by `(1 - account effective tax proxy)`, rounded up to cents and capped at that
   account's opening balance. Fixed-percentage strategy draws the supplied fraction of the
   beginning portfolio as a gross budget. Both follow the supplied account order exactly.
3. Account withdrawal tax = gross times proxy rounded to cents; net = gross minus tax.
   Return applies after withdrawals. Account end = account beginning minus gross withdrawal
   plus cent-rounded investment return. No account can become negative from the allowed rates.
4. Net income plus net withdrawals plus shortfall = net spending plus surplus. Surplus is
   disclosed and not reinvested. Sum account ending balances equals portfolio end, which becomes
   the next beginning balance. Summaries sum the rounded rows; no self-reported tie-out flags.
5. Spending shortfall is positive unfunded spending, even when assets remain because a fixed
   withdrawal policy draws too little. Asset depletion means ending portfolio equals zero.
   Depletion at the final row is by the horizon, not before it. Neither measure is a probability.

Tax rates are supplied effective withdrawal/income proxies, not statutory tax rules. The model
does not compute cost basis, brackets, gain realization, RMDs, Roth conversions, benefit
eligibility, household survivor transitions or long-term-care shocks. The supplied limitation
register must explicitly address these boundaries. An account labeled tax-free must have zero
withdrawal tax in this simplified model; questions about nonqualified distributions need an
external tax workflow. Healthcare must be present in supplied spending to affect the result.

A missing common assumption yields no unsupported projection. Missing scenario-specific data
leaves independent complete scenarios available. Material modeled shortfalls remain findings
for human planning review; exact arithmetic does not approve a retirement strategy.
