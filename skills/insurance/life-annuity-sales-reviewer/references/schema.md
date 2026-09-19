# Input and output contract

Use finite JSON with `case_id`, calendar `as_of`, `context` containing capacity, represented_party, object_id, jurisdiction and line_of_business; `sources` with unique source_ref, version and optional as_of; explicit `unresolved_issues` list; optional `upstream_artifacts`; and native `data`.

Every `data.profile` has profile_id, version, source_refs, reviewed_by, effective_from, effective_to, jurisdictions and lines_of_business. Freshness intervals are configured institution controls. Profiles and examples are not shipped jurisdiction law. The synthetic `US-TEST` fixture cannot establish any real state's requirements.

Malformed types, dates and financial values fail input validation. Missing business evidence usually remains a structured gap so a review packet can still be prepared. Amounts use finite nonnegative decimals; explicit zero differs from null. Results keep currency and amount definitions.

`data.transaction`: `product_type` (fixed-annuity/fixed-indexed-annuity/deferred-variable-annuity/variable-life/term-life/permanent-life), `distribution_channel`, `jurisdiction`, `replacement_status` (yes/no/unknown), `replacement_source_ref`. `profile.product_types` lists the reviewed supported classification; `additional_consumer_topics` and `additional_product_topics` extend the scaffold.

`consumer_evidence`, `product_evidence`, `replacement_evidence` are arrays of `topic`, scalar `value`, `source_ref`, `verified_on`. `profile.max_evidence_age_days` is a nonnegative configured integer; if absent, topic freshness is unresolved. Duplicate topic rows are deliberately unresolved; reconcile contradictory observations in source evidence and supply one reviewed summary with a clear source trail. Detailed source extracts remain separate from scalar summaries.

Use these exact topic strings. Missing required topics produce matrix gaps; these are engineering evidence topics, not a claim that every jurisdiction has an identical legal checklist.

| Evidence array / condition | Exact topics |
| --- | --- |
| `consumer_evidence`, all supported products | `insurance-needs`, `financial-objectives`, `liquidity-needs`, `funding-source`, `financial-capacity`, `age`, `time-horizon`, `risk-tolerance`, `financial-experience`, `tax-status` |
| `product_evidence`, all supported products | `charges`, `surrender-terms`, `guarantees`, `non-guaranteed-elements`, `restrictions`, `death-benefit`, `compensation-and-conflicts`, `disclosures-and-training` |
| `product_evidence`, fixed-annuity, fixed-indexed-annuity and deferred-variable-annuity | Also `annuitization-options`, `riders` |
| `product_evidence`, variable-life, term-life and permanent-life | Also `premium-obligations`, `coverage-duration` |
| `replacement_evidence`, when replacement_status is yes | `existing-values`, `existing-benefits`, `existing-charges`, `new-charges`, `lost-guarantees`, `new-surrender-period`, `replacement-rationale`, `retain-or-modify-alternative`, `replacement-disclosures` |

Each topic's value is a reviewed scalar summary (string, finite number or boolean), with null/empty string treated as unknown. An explicit zero or false is retained; it is not a finding that the evidence is favorable. A summary may itself describe unresolved facts; `evidence-present` does not mean that its substantive issue is resolved. Profile extensions add their exact strings to `additional_consumer_topics` or `additional_product_topics`. Other supplied topics remain in source_document but are not silently added to a matrix.

`alternatives`: `alternative_id`, `description`, `reason_reviewed`, `source_ref`, `verified_on`. `recommendation_rationale`: `text`, `source_ref`, `verified_on`. `applicability`: unique `rule_id`, `status` (applies/not-applicable/unknown), `authority_type` (enacted-law/regulator-rule/institution-policy), `source_ref`, `rationale`, `product_types`, `distribution_channels`. Required rule topics: state-sales-standard and state-replacement; variable products also require finra-2320, finra-2330 and regulation-bi determinations. Additional supplied rules are also checked.

`distribution_channel` is a nonempty profile-defined string. The exact value `registered-broker-dealer` is required for the evaluator to recognize broker-dealer/member capacity when checking an applicable FINRA or Regulation BI determination. Other channel values, such as `insurance-producer`, must match the corresponding applicability rows; they do not confer securities capacity. Applicability rows with institution-policy authority identify only an institution control, not an enacted-law determination.

Output contains consumer/product/replacement matrices, documented alternatives and applicability matrix. It has no suitability score, recommendation selection or principal approval.

The output preserves source_document and a content-bound artifact, separate completeness/evaluability, findings and unresolved issues. Human review is always required; approval is not_requested and execution is not_performed. Output validation recomputes the native result. Editable reviewer narrative belongs in a separate draft memo linked to this immutable calculation record. Hashes detect changes, not source authenticity.
