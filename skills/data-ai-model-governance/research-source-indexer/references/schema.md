# Native input and output contract

job_ref, as_of, purpose, catalog_version and sources. Each source has source_ref, doc_type, content_hash, published_at or effective_date, and entitlement {class, grant_ref where licensed/internal, use_permitted:true, reviewed_by, purpose, effective_from?, expires?}. Source refs are unique. Dates must be valid and not future at cutoff. Optional accessed_at is a supplied audit timestamp, never derived from as_of.

Outputs contain `input_hash` over every original JSON field and `source_truth: unverified`. Retain the original input separately; output validation requires `--input`. Embedded `source_input` is reserved for explicit internal use and must never be assumed suitable for downstream delivery. Unknown output fields and modified native results fail reconstruction. No source authenticity or execution authority is conveyed.

Read [domain-rules](domain-rules.md) for supported computations and unknown-state handling. All amounts must be finite; booleans do not substitute for numeric observations. Synthetic fixture extensions state illustrative bases only.
