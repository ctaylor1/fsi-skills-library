# Native schema

The `investment-foundation/1.0` request requires request_id, object_id, as_of, knowledge_cutoff, currency, audience=`internal-review`, versioned sources and optional unresolved_issues. Sources have source_ref, version, as_of and known_at; cited evidence must be eligible for the audience and cutoff. No `mode` or `extension` selector is supported.

- `initial_settled_cash` is nonnegative; `cash_source_ref` and `cash_as_of` identify the current snapshot, exactly matching review as_of.
- `policy` contains version, owner, source_ref, start_date/end_date (start >= review date), nonnegative minimum_cash and explicit_cost_budget, and cash_ordering=`outflows-before-inflows`.
- `positions[]` uses unique security_id with instrument_type=`cash-equity` or `etf`, unit=`shares`, currency, current_settled_quantity, target_quantity, positive reference_price, observed_on equal review date, buy_permitted/sell_permitted booleans and source_ref. Quantities are nonnegative.
- `proposed_slices[]` uses unique slice_id with known security_id, side=`buy` or `sell`, positive quantity and estimated_execution_price, nonnegative explicit_cost, currency, trade_date, settlement_date and source_ref. Start <= trade <= settlement <= end.
- `volume_assumptions[]` uses unique volume_id and unique security/trade_date pair, positive forecast_market_volume, maximum_participation in [0,1], unit=`shares`, source_ref. Every slice must bind one volume assumption.
- `external_cashflows[]` is an explicit possibly empty list with unique cashflow_id, signed amount, currency, settlement_date within horizon and source_ref.

Other collections must be nonempty and at most 10,000 records. Exact decimal strings preserve lexical precision; finite values are bounded by the shared foundation. Mixed currencies, unsupported instruments/units, stale opening snapshots, duplicate IDs and impossible schedule dates fail validation. Business breaches yield a needs-review draft with all projected quantities and dated constraints retained.

Outputs contain slices, aggregate participation, settlement_cash_path, delivery_checks, target_reconciliation, estimated cost components, projected_final_cash and a bounded schedule_candidate flag. Execution authority is false. Original-input hash and detached reconstruction protect consistency, not source truth or professional acceptance.

