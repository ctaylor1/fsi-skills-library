# Input and output contract

Use finite JSON with `case_id`, calendar `as_of`, `context` containing capacity, represented_party, object_id, jurisdiction and line_of_business; `sources` with unique source_ref, version and optional as_of; explicit `unresolved_issues` list; optional `upstream_artifacts`; and native `data`.

Every `data.profile` has profile_id, version, source_refs, reviewed_by, effective_from, effective_to, jurisdictions and lines_of_business. Freshness intervals are configured institution controls. Profiles and examples are not shipped jurisdiction law. The synthetic `US-TEST` fixture cannot establish any real state's requirements.

Malformed types, dates and financial values fail input validation. Missing business evidence usually remains a structured gap so a review packet can still be prepared. Amounts use finite nonnegative decimals; explicit zero differs from null. Results keep currency and amount definitions.

`data.entities`: objects with `entity_id`, `kind` and `legal_name`; `data.requirements`: unique `requirement_id`, `entity_id`, `jurisdiction`, `line_of_authority`, `carrier_id`, `license_required` and `appointment_required` (boolean or null), and `rule_source_ref`. No requirements is a scope gap.

`data.licenses` and `data.appointments`: `record_id`, `entity_id`, `entity_name`, `jurisdiction`, `line_of_authority`, `status`, `effective_from`, `effective_to` (or sourced `non_expiring: true`), `verified_on`, `source_ref`; appointments additionally need `carrier_id`. Statuses active/inactive/suspended/revoked/terminated are observed record values. Other or absent statuses remain unknown. Multiple records for the same requirement are retained as unresolved.

`profile.max_evidence_age_days` is a nonnegative institution-selected integer. A missing interval cannot clear credential evidence. Output `results.scope_checks` retains requested scope, matched record IDs, source references and per-check reasons. The output never asserts binding authority.

The output preserves source_document and a content-bound artifact, separate completeness/evaluability, findings and unresolved issues. Human review is always required; approval is not_requested and execution is not_performed. Output validation recomputes the native result. Editable reviewer narrative belongs in a separate draft memo linked to this immutable calculation record. Hashes detect changes, not source authenticity.
