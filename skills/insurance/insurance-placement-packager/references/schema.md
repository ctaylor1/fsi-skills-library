# Input and output contract

Use finite JSON with `case_id`, calendar `as_of`, `context` containing capacity, represented_party, object_id, jurisdiction and line_of_business; `sources` with unique source_ref, version and optional as_of; explicit `unresolved_issues` list; optional `upstream_artifacts`; and native `data`.

Every `data.profile` has profile_id, version, source_refs, reviewed_by, effective_from, effective_to, jurisdictions and lines_of_business. Freshness intervals are configured institution controls. Profiles and examples are not shipped jurisdiction law. The synthetic `US-TEST` fixture cannot establish any real state's requirements.

Malformed types, dates and financial values fail input validation. Missing business evidence usually remains a structured gap so a review packet can still be prepared. Amounts use finite nonnegative decimals; explicit zero differs from null. Results keep currency and amount definitions.

`data.placement`: `placement_id`, `insured_id`. `data.market_responses`: `response_id` (unique), `market_id`, `version`, `source_ref`, `issued_on`, `valid_until`, `insured_id`, `jurisdiction`, `line_of_business`, `status` (quoted/declined/no-response). Quote fields: `currency`, `period_start`, `period_end`, `layer`, `coverage_basis`, `coverages` array, `exclusions` array, `limit`, `retention`, `premium`, `fees`, `taxes` (decimal strings or null).

Each quote carries `subjectivities`: objects with `subjectivity_id`, `description`, `status` (satisfied/open/waived-by-carrier/unknown) and `evidence_source_ref` for satisfied/waived items. `data.selected_versions` maps market ID to response ID when there are multiple records. Single supplied versions may be reviewed directly; their authenticity and completeness remain unverified.

Output retains `response_history`, `selected_response_ids`, `market_assessments` and `comparable_groups`. `quoted_total` is null when identity, temporal, financial or term evidence is unresolved. `market_selection` and `binding_status` remain not-performed.

The output preserves source_document and a content-bound artifact, separate completeness/evaluability, findings and unresolved issues. Human review is always required; approval is not_requested and execution is not_performed. Output validation recomputes the native result. Editable reviewer narrative belongs in a separate draft memo linked to this immutable calculation record. Hashes detect changes, not source authenticity.
