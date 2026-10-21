# Event mechanics and interpretation

The method applies one event to a fixed supplied baseline. It does not model
intervening operations, other transactions, purchase accounting, instrument
conversion, an ownership-control analysis, weighted-average EPS or a share-price
response. Use announced/proposed calculations as conditional mechanical scenarios;
do not present those balances as reported facts. Completed status remains the
caller's sourced assertion. No event is closed, financed or executed by this skill.

For every event, `after = baseline + change` and `net_debt = debt - cash`.
All money and shares retain the declared currency, numeric scale, accounting and
consolidation scope, security, class and count basis. New-share fraction means
`new_shares / post_event_shares`, a count fraction, not voting/economic dilution.
Share-count change fraction is `change_in_shares / opening_shares`.

| Event | Cash/debt/share mechanics |
| --- | --- |
| Primary equity raise | Gross proceeds = new shares × price. Cash increases by gross proceeds less fees; shares increase by newly issued shares. This is primary issuance; secondary owner sales are excluded. |
| Repurchase | Shares decrease by repurchase spend ÷ price. Fees do not buy shares. Cash decreases by cash funding; debt increases by debt funding. Cash funding + debt funding must equal spend + fees. |
| Acquisition | Cash changes by acquired cash − buyer cash funding; debt increases by new funding + target debt assumed; shares increase by stock consideration shares. Cash + debt + stock consideration must equal equity purchase price + fees. Implied acquired EV = equity purchase price + debt assumed − acquired cash. Acquired cash is included in the post-close bridge; it is not counted as an upfront financing source. |
| Refinancing | Debt changes by new proceeds − principal repaid; cash changes by retained proceeds − cash funding. New proceeds + cash funding must equal principal repaid + fees + cash retained. Annual tranche interest change = new proceeds × new rate − repaid principal × old rate, excluding tax and fee amortization. |
| Asset disposal | Cash increases by sale cash proceeds less cash leaving with the business, fees and taxes; debt decreases by debt transferred. Proceeds are explicitly cash proceeds; a supplied enterprise value is not substituted for cash consideration. No book gain is calculated. |

Funding sources/uses use a relative `1e-9` numerical tolerance only. A material
unexplained plug rejects intake. Funding reconciliation does not authenticate a
commitment or assess legal availability, restricted cash or covenant compliance.
For acquisition, repurchase and refinancing, the supplied `cash_funding` is an
upfront requirement against available baseline cash. Acquired cash and retained
refinancing proceeds arrive after that cash-funded leg in this bounded sequence;
they cannot silently fund an earlier payment. Other settlement sequencing or a
temporary bridge facility needs separate evidenced review and is not inferred.

`upfront_cash_required` is that cash-funded leg, with the separately reported
`upfront_cash_available_from_baseline` and `upfront_cash_shortfall`. Equity raise
and disposal fees/taxes are netted from their respective proceeds; those modes
have no separately supplied upfront cash-funded leg. `ending_cash_shortfall`
retains a negative post-event cash bridge. `additional_cash_required` is the
maximum of upfront and ending shortfalls, not their sum: those gaps may overlap.
`cash_feasible_for_supplied_bridge` is false if either shortfall exists, and an
unresolved issue survives even when post-event cash is nonnegative. For example,
cash funding 90 against baseline cash 80 needs an unestablished 10 upfront even if
10 of acquired cash leaves ending cash at zero. A completed event with a gap still
requires reconciliation of missing financing/intervening cash flows.

Event interactions, multiple share classes, debt discounts/premiums, earnouts,
contingent consideration, currency conversions, stock splits, spin-offs, rights
issues, in-kind disposals and leveraged EPS accretion require further specialized
review. Do not force them into a similarly named supported mode.
