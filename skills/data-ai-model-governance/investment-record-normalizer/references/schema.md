# Native input and output contract

bundle_id, as_of, ruleset_version, records; optional inline ruleset {version, field_maps, enums}. Each record: source_system, source_record_id, source_as_of, record_type, payload; optional position_basis, quantity_unit, lot_id, effective_at, identity_candidates. Required canonical fields: position account_id/security_id/quantity/currency; cash account_id/currency/amount; order account_id/order_ref/side/security_id/quantity/currency; transaction account_id/txn_ref/txn_type/amount/currency/trade_date.

Outputs contain `input_hash` over every original JSON field and `source_truth: unverified`. Retain the original input separately; output validation requires `--input`. Embedded `source_input` is reserved for explicit internal use and must never be assumed suitable for downstream delivery. Unknown output fields and modified native results fail reconstruction. No source authenticity or execution authority is conveyed.

Read [domain-rules](domain-rules.md) for supported computations and unknown-state handling. All amounts must be finite; booleans do not substitute for numeric observations. Synthetic fixture extensions state illustrative bases only.
