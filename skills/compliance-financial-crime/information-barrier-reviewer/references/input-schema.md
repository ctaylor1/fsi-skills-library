# Native input schema

The common `compliance-foundation/2.0` envelope is specified in the bundled foundation contract.
The `data` object contains exactly the following native records.

requests[]: request_id, operation, person_id, information_ids, classification, purpose, need_to_know, starts_on, ends_on, authority_person_id, authority_information_ids, authority_purpose, authority_starts_on, authority_ends_on, authority_scope, restrictions, list_changes; every consequential field is a fact. operation is wall-crossing, access or list-change; need_to_know is true, false or null. Classification is public, confidential, MNPI or unknown. No script decides legal materiality.

A fact holds `value`, `source_refs` and `fact_ids` under the common contract; use null with explicit unknown/conflict source status when unavailable. Match exact value and type to the mapped source fact, including empty/zero/false facts. Identity values are not interchangeable across cases. Unknown fields and malformed dates/counts stop intake. Substantive missingness proceeds only as an unresolved draft.

Native object_type: `information_barrier_review`. The executable `domain.py` schema is authoritative for the exact required fields/types; all data record IDs are internal labels, and consequential identity/context values are claims.

## Complete field inventory

Each listed consequential field is an exact claim object `{value, source_refs, fact_ids}`.
Only the row label named below is a plain internal ID. Empty evidence-reference lists preserve
unknowns; malformed types/fields stop intake.

- `data.requests[]`: row label `request_id`; claims `operation`, `person_id`, `information_ids`, `classification`, `purpose`, `need_to_know`, `starts_on`, `ends_on`, `authority_person_id`, `authority_information_ids`, `authority_purpose`, `authority_starts_on`, `authority_ends_on`, `authority_scope`, `restrictions`, `list_changes`.
