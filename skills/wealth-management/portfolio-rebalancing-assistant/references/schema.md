# Transition schema v0.2

Common wealth-p0-v1 envelope: request/household, ISO as_of, US professional capacity and dated sources.
Every material record below carries source_ids. Numeric fields are finite nonnegative JSON numbers;
null/omitted material facts remain unknown. Containers/IDs are required. v0.1 approvals/execution tokens,
partial plan hashes and proportional position-level tax estimates are not migrated automatically.

- account: account_id, currency, taxable boolean/null, source_ids.
- portfolio: cash (settled cash available at snapshot), reported_total_value,
  positions_complete boolean, source_ids, positions list. Empty positions with complete:true means
  cash-only; absent holdings never mean zero when completeness is unknown.
- Position: unique security_id, quantity, reported_market_value, optional reported_cost_basis,
  source_ids, lots list. Lots have globally unique lot_id, quantity, total cost_basis,
  acquired_on ISO date, source_ids. Taxable positions require complete lots.
- universe: unique security_id, currency, price, quote_on, quantity_increment, fee_bps, fixed_fee,
  settles_on (default proposed settlement for generated drafts), optional tax_identity_group,
  source_ids. Include every current and target security; no FX, shorting or derivatives are supported.
- target: target_id, version, selection_reference (human's supplied selection evidence, not authenticated),
  cash_weight, source_ids, allocations [{security_id, weight, source_ids}]. All current positions need
  explicit weights, including zero for exits. Target weights plus cash equal one.
- policy: policy_id, version, owner, source_ids, max_order_notional, max_sell_turnover (fraction),
  minimum_cash, max_position_weight (fraction), drift_tolerance_weight (fraction), restrictions
  [{security_id, buy_allowed, sell_allowed, source_ids}]. Explicitly cover all held/target/traded names.
  Unknown permission is not allowed. These are supplied planning limits, not proof of actual authority.
- intent: mode generate|validate, reason, trade_date, lot_selection oldest-first|specified,
  settlement_policy same-day-netting|prefund-buys, transaction_cost_budget (explicit reserve), source_ids.
  Generate mode supports oldest-first only; validate mode can preserve explicit lot choices.
- trades (validate mode only): unique trade_id, security_id, side buy|sell, quantity, fee_amount,
  settles_on, source_ids, lot_allocations [{lot_id, quantity, source_ids}]. An empty list is a valid
  no-trade review, subject to remaining target drift. Generated mode does not accept caller trades.

Result includes input_snapshot, full plan_hash, trades with per-trade intent_binding, cash/position/NAV
reconciliation, dated settlement ledger, lot basis/gain arithmetic, turnover and residual drift,
execution_status:not-supported and approval_status:not-authenticated. Unknown economics are null.
The output validator reconstructs the entire draft; changing fees, restrictions, source IDs, intent,
settlement, lot choices, quantities or action posture breaks verification against the held input.


## Required upstream issue contract
`upstream_issues` is an explicit list of `{artifact_id, code, message,
status: unresolved|resolved, source_ids}`. Identifiers and message must be nonempty strings;
source_ids must be a list resolving to the envelope registry. Missing/malformed issue structures
reject input; missing/unknown citations remain source-gap findings. Any unresolved issue forces
needs-data regardless of local arithmetic or model consistency. Resolved records remain in the
result and handoff context; status is a supplied reviewer representation, not authenticated closure.
Use an empty list only after reviewing the originating artifacts for material unresolved concerns.

Output `result.upstream_issues` and `result.handoff_context.upstream_issues` preserve every record;
the context also preserves household, date, capacity and source registry. Original code and artifact
identity accompany propagated findings. Recomputing output detects omitted issues/context relative
to the held input. It cannot detect a consistently rewritten source artifact or falsely claimed resolution.
Top-level `unresolved_issues` from another schema is rejected until explicitly mapped; it is never
silently ignored. Earlier draft inputs without this list require source review before migration.
