# Native input and output contract

entity, as_of, config_version, internal_source, vendor_source, internal_observations, vendor_observations, optional config. Rows: instrument_id, domain, field, value, as_of, source_ref; numeric comparisons require explicit equal unit; prices require explicit equal currency. Optional valuation_date distinguishes economic from observation dates. One observation per cell per side.

Outputs contain `input_hash` over every original JSON field and `source_truth: unverified`. Retain the original input separately; output validation requires `--input`. Embedded `source_input` is reserved for explicit internal use and must never be assumed suitable for downstream delivery. Unknown output fields and modified native results fail reconstruction. No source authenticity or execution authority is conveyed.

Read [domain-rules](vendor_feed-domain-rules.md) for supported computations and unknown-state handling. All amounts must be finite; booleans do not substitute for numeric observations. Synthetic fixture extensions state illustrative bases only.
