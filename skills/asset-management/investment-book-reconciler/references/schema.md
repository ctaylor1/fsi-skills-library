# Native input and output contract

entity, as_of, config_version, base_currency, internal_records, external_records; optional doc position_basis and config. Rows: record_id, match_key, account, source_system, record_type, source_ref, date, currency, quantity for position or amount for cash. Positions require quantity_unit; all rows require position_basis on row or job. Optional security_id, settle_date, settlement_evidence_ref, duplicate_of, route_hint. Config aggregation_mode is one-to-one (default) or sum; FX is rate-to-base.

Outputs contain `input_hash` over every original JSON field and `source_truth: unverified`. Retain the original input separately; output validation requires `--input`. Embedded `source_input` is reserved for explicit internal use and must never be assumed suitable for downstream delivery. Unknown output fields and modified native results fail reconstruction. No source authenticity or execution authority is conveyed.

Read [domain-rules](domain-rules.md) for supported computations and unknown-state handling. All amounts must be finite; booleans do not substitute for numeric observations. Synthetic fixture extensions state illustrative bases only.

## Supported decimal bounds

Supply decimal strings when every input digit matters. Each numeric input supports at most 38 coefficient digits (including retained trailing zeros), a Decimal exponent between -38 and +38, and a nonzero adjusted exponent between -38 and +38. Numeric literals are limited to 256 characters; booleans and non-finite values are rejected. The job supports at most 100,000 total input records/lines. Amounts, tolerances, materiality thresholds and supplied FX rates use these bounds. Unsupported values fail before a result is emitted.

All arithmetic, including aggregation, differences, tolerance/materiality checks and any FX multiplication, uses a private 256-digit Decimal context with inexact/rounding traps. The process-global context is unchanged. Derived results can contain more than 38 digits; the input limits plus row bound make the supported operations exact within the working context. These are software precision limits, not instrument conventions or economic materiality policies.
