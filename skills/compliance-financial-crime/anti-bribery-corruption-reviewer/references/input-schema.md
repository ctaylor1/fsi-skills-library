# Native input schema

The common `compliance-foundation/2.0` envelope is specified in the bundled foundation contract.
The `data` object contains exactly the following native records.

engagements[]: engagement_id, benefit_type, recipient, services, delivered_services, amount, benchmark_amount, currency, benchmark_currency, proportionality_limit, government_link, due_diligence_complete, policy_applies, counterevidence. All fields are facts; numeric amount and benchmark_amount are finite nonnegative values or null. Limit is a supplied institutional benchmark, never law.

A fact holds `value`, `source_refs` and `fact_ids` under the common contract; use null with explicit unknown/conflict source status when unavailable. Match exact value and type to the mapped source fact, including empty/zero/false facts. Identity values are not interchangeable across cases. Unknown fields and malformed dates/counts stop intake. Substantive missingness proceeds only as an unresolved draft.

Native object_type: `abc_engagement_review`. The executable `domain.py` schema is authoritative for the exact required fields/types; all data record IDs are internal labels, and consequential identity/context values are claims.

## Complete field inventory

Each listed consequential field is an exact claim object `{value, source_refs, fact_ids}`.
Only the row label named below is a plain internal ID. Empty evidence-reference lists preserve
unknowns; malformed types/fields stop intake.

- `data.engagements[]`: row label `engagement_id`; claims `benefit_type`, `recipient`, `services`, `delivered_services`, `amount`, `benchmark_amount`, `currency`, `benchmark_currency`, `proportionality_limit`, `government_link`, `due_diligence_complete`, `policy_applies`, `counterevidence`.
