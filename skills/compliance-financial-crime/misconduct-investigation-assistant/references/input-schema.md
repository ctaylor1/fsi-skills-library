# Native input schema

The common `compliance-foundation/2.0` envelope is specified in the bundled foundation contract.
The `data` object contains exactly the following native records.

mandate: authorized, allegation_ids, allowed_evidence_types, legal_owner, hr_owner; allegations[]: allegation_id, description; events[]: event_id, allegation_id, occurred_on, proposition, evidence_type, hypothesis, polarity; plans[]: plan_id, allegation_id, evidence_type, purpose. All mandate/event/plan fields other than record IDs are facts. polarity is supports, contradicts or neutral.

A fact holds `value`, `source_refs` and `fact_ids` under the common contract; use null with explicit unknown/conflict source status when unavailable. Match exact value and type to the mapped source fact, including empty/zero/false facts. Identity values are not interchangeable across cases. Unknown fields and malformed dates/counts stop intake. Substantive missingness proceeds only as an unresolved draft.

Native object_type: `misconduct_investigation`. The executable `domain.py` schema is authoritative for the exact required fields/types; all data record IDs are internal labels, and consequential identity/context values are claims.

## Complete field inventory

Each listed consequential field is an exact claim object `{value, source_refs, fact_ids}`.
Only the row label named below is a plain internal ID. Empty evidence-reference lists preserve
unknowns; malformed types/fields stop intake.

- `data.mandate`: `authorized`, `allegation_ids`, `allowed_evidence_types`, `legal_owner`, `hr_owner`.
- `data.allegations[]`: row label `allegation_id`; claims `description`.
- `data.events[]`: row label `event_id`; claims `allegation_id`, `occurred_on`, `proposition`, `evidence_type`, `hypothesis`, `polarity`.
- `data.plans[]`: row label `plan_id`; claims `allegation_id`, `evidence_type`, `purpose`.
