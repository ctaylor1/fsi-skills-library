# Native input and output contract

entity, as_of, config_version, source_hierarchy, securities. Each unique security_key has identifiers[{scheme,value,source,as_of,source_ref?,effective_date?}] and attributes[{field,value,source,as_of,source_ref?,effective_date?}]. Fields: currency, exchange, asset_class, maturity, coupon, rating, benchmark, issuer. Optional config controls required/material fields, freshness and numeric tolerance.

Outputs contain `input_hash` over every original JSON field and `source_truth: unverified`. Retain the original input separately; output validation requires `--input`. Embedded `source_input` is reserved for explicit internal use and must never be assumed suitable for downstream delivery. Unknown output fields and modified native results fail reconstruction. No source authenticity or execution authority is conveyed.

Read [domain-rules](domain-rules.md) for supported computations and unknown-state handling. All amounts must be finite; booleans do not substitute for numeric observations. Synthetic fixture extensions state illustrative bases only.
