# Native input schema

The common `compliance-foundation/2.0` envelope is specified in the bundled foundation contract.
The `data` object contains exactly the following native records.

finding: finding_id, version, accepted, affected_scope, closure_owner, closure_authority; criteria[]: criterion_id, finding_id, finding_version, required_scope, required_operation_from, required_operation_to, minimum_observations; evidence[]: evidence_id, criterion_id, finding_id, finding_version, scope, type, operation_from, operation_to, observations, failures, evidence_complete. Fields other than IDs are facts; type is design, implementation, retest or sustained-operation. No actual closure status is produced.

A fact holds `value`, `source_refs` and `fact_ids` under the common contract; use null with explicit unknown/conflict source status when unavailable. Match exact value and type to the mapped source fact, including empty/zero/false facts. Identity values are not interchangeable across cases. Unknown fields and malformed dates/counts stop intake. Substantive missingness proceeds only as an unresolved draft.

Native object_type: `compliance_remediation_review`. The executable `domain.py` schema is authoritative for the exact required fields/types; all data record IDs are internal labels, and consequential identity/context values are claims.

## Complete field inventory

Each listed consequential field is an exact claim object `{value, source_refs, fact_ids}`.
Only the row label named below is a plain internal ID. Empty evidence-reference lists preserve
unknowns; malformed types/fields stop intake.

- `data.finding`: `finding_id`, `version`, `accepted`, `affected_scope`, `closure_owner`, `closure_authority`.
- `data.criteria[]`: row label `criterion_id`; claims `finding_id`, `finding_version`, `required_scope`, `required_operation_from`, `required_operation_to`, `minimum_observations`.
- `data.evidence[]`: row label `evidence_id`; claims `criterion_id`, `finding_id`, `finding_version`, `scope`, `type`, `operation_from`, `operation_to`, `observations`, `failures`, `evidence_complete`.

For design/implementation artifacts only, operating dates/counts/failures are not applied as evidence and may be null. Their source bindings remain visible in the detached contract. Retest/sustained-operation artifacts require those fields to be supported; null withholds the criterion. Supplemental design does not replace or invalidate independently sufficient operating evidence.

`finding.closure_criterion_ids` is a required source-backed list of every original accepted closure criterion. Its distinct IDs must match the supplied criterion record inventory exactly; omitted or invented criteria withhold closure-evidence sufficiency.
