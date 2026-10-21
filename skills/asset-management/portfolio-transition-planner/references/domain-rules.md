# Bounded transition method

Only single-currency long-only cash-equity and ETF shares are supported. Initial quantities are settled, unencumbered and available at the same review snapshot as initial cash. The proposed trade and settlement dates are supplied calendar dates, never inferred from a regulatory cycle or exchange calendar. All slices settle within the explicit horizon.

For each security/trade date, participation is the gross sum of buy and sell share quantities divided by the single supplied forecast market volume. Compare the unrounded aggregate quantity with volume times cap; slicing an order cannot evade the cap. The result is a forecast condition, not proof of available market liquidity.

Apply sells before buys to the trade-date position and separately to settled share inventory on settlement dates. Compare deliveries with previously settled shares, excluding same-day receipts. These conservative checks do not model custody account transfers, failures, borrow availability or corporate actions.

A buy settles as a cash outflow of quantity times estimated execution price, plus its explicit fee. A sell brings the estimated notional as an inflow while its fee is an outflow. External flows have explicit signed amounts and settlement dates. For each date, minimum cash is opening cash minus all outflows; closing cash adds same-day inflows. This convention does not assert intraday availability or legal cash netting. Preserve any initial or dated minimum breach.

Projected final quantities are current settled quantity plus proposed buys minus proposed sells and must reconcile to supplied targets. Explicit costs sum independently against the supplied explicit-cost budget. Estimated reference slippage is `q * (estimated_price - reference_price)` for a buy and `q * (reference_price - estimated_price)` for a sell. Negative slippage is retained as a favorable supplied-price difference. Combined estimated cost adds explicit fees. These estimates exclude delay, opportunity, tax, impact-model and unexecuted-order costs and are not realized implementation shortfall.

All sums and comparisons use exact bounded decimals. Displayed participation ratios round to 12 places without controlling threshold decisions. Missing values are never zero. The helper compares one supplied schedule; it does not optimize sequence, estimate nonlinear impact or evaluate alternative targets.

