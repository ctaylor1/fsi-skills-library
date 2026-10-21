# Native input and output contract

firm_id,as_of (month-end),ruleset_version,ruleset_effective_date,measurement_frequency:monthly,policy_scope_reviewed:true,composites,portfolios. Composite requires composite_id,strategy,min_asset_value,inclusion_lag_months,requires_discretionary:boolean,rule_id,rule_version,effective_date. Portfolio requires portfolio_id,strategy,discretionary:boolean,fee_paying:boolean,composite_required:boolean,market_value,under_mgmt_date,assigned_composite_ids,source_ref; optional termination_date and significant_cash_flow_pct.

Outputs contain `input_hash` over every original JSON field and `source_truth: unverified`. Retain the original input separately; output validation requires `--input`. Embedded `source_input` is reserved for explicit internal use and must never be assumed suitable for downstream delivery. Unknown output fields and modified native results fail reconstruction. No source authenticity or execution authority is conveyed.

Read [domain-rules](domain-rules.md) for supported computations and unknown-state handling. All amounts must be finite; booleans do not substitute for numeric observations. Synthetic fixture extensions state illustrative bases only.
