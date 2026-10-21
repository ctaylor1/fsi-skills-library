# Native input and output contract

portfolio_id, as_of, config_version, instruments[{instrument_key,asset_class,source_ref,held?,nav_impacting?,identifiers?,exchange?,currency?}], prices, factors, classifications, mappings, optional config. Price moves require prev_price_asof before price_asof and comparison_basis_reviewed:true. Factor rows require as_of. Classification rows require as_of and feed.

Outputs contain `input_hash` over every original JSON field and `source_truth: unverified`. Retain the original input separately; output validation requires `--input`. Embedded `source_input` is reserved for explicit internal use and must never be assumed suitable for downstream delivery. Unknown output fields and modified native results fail reconstruction. No source authenticity or execution authority is conveyed.

Read [domain-rules](data_quality-domain-rules.md) for supported computations and unknown-state handling. All amounts must be finite; booleans do not substitute for numeric observations. Synthetic fixture extensions state illustrative bases only.

Classification-conflict exceptions route to `investment-data-quality-reviewer` with `route_mode: vendor_feed` and `handoff_status: requires_reviewed_mapping`. The source snapshot is not the cross-source mode request; a reviewer must prepare and validate the separate native request.
