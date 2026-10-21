# Native input and output contract

as_of, book, config_version, instruments. Instrument: instrument_id,asset_class,source_ref,currency,unit,candidate_prices; optional prior_price,prior_price_date,prior_price_comparable,comparison_source_id,market_value_base,liquidity_class,open_challenge. Candidate: source_id,source_type,price,as_of,currency,unit,evidence_kind in observation/estimate/indicative/carry_forward. Estimates require method and method_approved:true. Optional fair_value_level requires hierarchy_reviewed_by.

Outputs contain `input_hash` over every original JSON field and `source_truth: unverified`. Retain the original input separately; output validation requires `--input`. Embedded `source_input` is reserved for explicit internal use and must never be assumed suitable for downstream delivery. Unknown output fields and modified native results fail reconstruction. No source authenticity or execution authority is conveyed.

Read [domain-rules](domain-rules.md) for supported computations and unknown-state handling. All amounts must be finite; booleans do not substitute for numeric observations. Synthetic fixture extensions state illustrative bases only.
