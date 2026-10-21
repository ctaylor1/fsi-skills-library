# Native input schema

The common `compliance-foundation/2.0` envelope is specified in the bundled foundation contract.
The `data` object contains exactly the following native records.

test: mandate_type, mandate_owner, independent_assessment, operational_involvement, conflict_review, population_ids, sample_ids, sampling_method, maximum_failures, procedure; observations[]: item_id, outcome, performed_on, procedure, evidence_complete. All fields except item_id are facts. outcome is pass, fail or unknown. Mandate type is operational-qa, second-line-monitoring, independent-testing, model-validation or internal-audit.

A fact holds `value`, `source_refs` and `fact_ids` under the common contract; use null with explicit unknown/conflict source status when unavailable. Match exact value and type to the mapped source fact, including empty/zero/false facts. Identity values are not interchangeable across cases. Unknown fields and malformed dates/counts stop intake. Substantive missingness proceeds only as an unresolved draft.

Native object_type: `compliance_control_test`. The executable `domain.py` schema is authoritative for the exact required fields/types; all data record IDs are internal labels, and consequential identity/context values are claims.

## Complete field inventory

Each listed consequential field is an exact claim object `{value, source_refs, fact_ids}`.
Only the row label named below is a plain internal ID. Empty evidence-reference lists preserve
unknowns; malformed types/fields stop intake.

- `data.test`: `mandate_type`, `mandate_owner`, `independent_assessment`, `operational_involvement`, `conflict_review`, `reporting_line_review`, `tester_competence_review`, `population_ids`, `sample_ids`, `sampling_method`, `maximum_failures`, `procedure`, `control_id`, `control_objective`, `window_from`, `window_to`.
- `data.observations[]`: row label `observation_id`; claims `item_id`, `outcome`, `performed_on`, `procedure`, `evidence_complete`, `control_id`.
