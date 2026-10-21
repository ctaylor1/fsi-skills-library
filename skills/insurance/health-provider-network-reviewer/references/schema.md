# Native input schema

Required envelope: `case_id` durable nonblank string; `as_of` YYYY-MM-DD;
`context` object with nonblank `capacity`, `represented_party`, `object_id`,
`jurisdiction`, `line_of_business`; `sources` array of unique objects containing
`source_ref`, `version`, `as_of`, `locator`; `unresolved_issues` explicit string
array; `data` object. Source dates must be no later than as_of. Unknown context may
be the literal unknown and keeps the result partial. No extra field grants authority.

`data.owner`, `market`, `program`, `product`, `source_locator`, `inventory_statement`,
`reviewed_by`, `reviewed_on` and `source_refs` are required. The statement must
expressly support the completeness/review claims and name the inventory scope;
review dates cannot postdate as_of. Source references resolve to the envelope and
locators identify evidence within those sources. A reviewer name does not prove
review. Model extraction must preserve null where the raw source is silent.

The profile is **data.profile**, never top-level. It requires `profile_id`,
`version`, `reviewed_by`, `source_refs`, `method`, inclusive `effective_from` and
`effective_to` around as_of, `jurisdictions` including context.jurisdiction,
`lines_of_business` including context.line_of_business, `markets`, `programs`,
`products` including actual data values, `rule_basis`, and `limitations`. Arrays
are explicit strings. These are supplied scope evidence, not adopted rule packs.

All fields below are required except an explicit optional field or conditional
field. Text is nonblank; no unknown/n/a substitute establishes evidence. Dates are
YYYY-MM-DD. Numeric values use finite exact decimal strings or integer JSON numbers;
fractional JSON floats, booleans and NaN/infinity are rejected. Numeric null means
unknown, never zero. Values are nonnegative unless expressly signed; proportions
are in [0,1]; stated integer fields must be whole. All inventories are arrays of
objects, at most 10000 rows each, with unique nonblank identity fields. Each record
has `source_refs` and `source_locator` unless stated otherwise. An explicit empty
array is different from unknown/null. Evidence gaps preserve a valid needs-data
artifact with dependent results null; malformed types reject input.

Optional `upstream_artifacts` and `context_mappings` use workflow-contract.md.
Unresolved upstream/input issues withhold derived results. Reviewed context mapping
must bind source artifact hash, source_context, target_context, reviewed_by, basis
and source_refs. No mapping removes inherited issues.

## Network profile and data

`context.capacity` is exactly `health-network-review`, `line_of_business` is
`health`, and `object_id` equals data.plan_id. data.reviewed_on must be on or after
observed_on.


`profile.method` is exactly `reviewed-health-network-access-v1`. `data` additionally
requires `plan_id`, `population_basis`, `observed_on` date <= as_of,
`provider_inventory_complete`, `member_population_complete`,
`measurement_inventory_complete`, `threshold_inventory_complete` (boolean/null),
`weighting` exactly `one-per-unique-member-per-threshold`,
`expected_provider_record_ids` unique string array (may be empty),
`expected_threshold_ids` unique nonempty string array, and inventories below.
All complete flags must be explicitly supported by the cited inventory statement.

| Inventory / nested object | Exact required fields and semantics |
| --- | --- |
| `providers[]` | May be empty only with affirmative complete inventory. Unique `provider_record_id`; exact text `provider_id`, `site_id`, `specialty_id`, `geography_id`; source_refs, source_locator; optional `npi` text/null; nested contract, credentials, directory. Composite provider/site/specialty must be unique; multiple distinct sites remain separate. |
| `providers[].contract` | `contract_id`, `version`, `plan_id` equal data.plan_id; `status` exactly `executed` or `not-executed`; ordered inclusive `effective_from`, `effective_to`; source_refs, source_locator. Unknown dates/status are gaps. |
| `providers[].credentials` | `credential_evidence_id`, `license_evidence_id`, `reviewed_by`; `credential_status`, `license_status` each exactly `verified` or `not-current`; `reviewed_on` <= observed_on, `next_review_due` >= reviewed_on; source_refs, source_locator. Unknown status or absent evidence is a gap. Due before observed_on is a known expired review and excludes the record. |
| `providers[].directory` | `observed_on` equal data.observed_on; `present` boolean/null; source_refs, source_locator. Null is a gap. Directory presence is a separate observation. |
| `thresholds[]` | Unique `threshold_id`; `plan_id` equals data.plan_id; `market`, `program`, `product` match data; `specialty_id`, `geography_id`; `population_basis` equals data; `metric` exactly `distance` or `time`; `unit` miles/kilometers for distance, minutes for time; `travel_mode` driving/walking/transit; nonnegative `maximum_value`; positive integer `minimum_distinct_providers`; `required_member_fraction` in [0,1]; `rule_basis`, `version`, `reviewed_by`; effective_from/effective_to covering observed_on; source_refs, source_locator. |
| `populations[]` | Unique `population_id`; `threshold_id` existing threshold, exactly one population per threshold; `plan_id`, `specialty_id`, `geography_id`, `population_basis` identical to threshold; `complete` boolean/null; unique text array `member_ids`; integer `eligible_member_count` exactly equal member count; source_refs, source_locator. Zero population has undefined fraction and comparison. |
| `measurements[]` | May be empty if there are no eligible candidate providers. Unique `measurement_id`; `threshold_id`, `member_id`, `provider_record_id`; `plan_id`, `specialty_id`, `geography_id`, `metric`, `unit`, `travel_mode` identical to threshold; `observed_on` equal data; `measurement_method`; nonnegative `value`; source_refs, source_locator. Member must belong to that threshold population and provider must have matching specialty/geography. |

Require exactly one travel measurement for each threshold/member/eligible
provider-site tuple. Duplicate tuples are gaps even with different measurement IDs.
Extra measurements for supplied ineligible providers are retained but cannot qualify;
unknown or misaligned evidence still withholds metrics. No inferred nearest provider,
unit conversion, geographic mapping or extrapolation from sampled members is allowed.
Every threshold and provider ID must reconcile to its expected complete inventory.

Eligible provider-site means executed plan-matching contract covering observation,
explicit verified credential/license evidence, and current reviewed-through date.
Count distinct provider_id within the threshold limit for each member, never site
count. Members each weigh one for each specialty/geography/threshold; do not aggregate
percentages across thresholds or count specialty tests as distinct people.

`results.provider_inventory[]` retains provider_record_id, provider_id, site_id,
specialty_id, source_refs, contract_active, credential_current, directory_present,
eligible_for_supplied_access_test. `access_comparisons[]` retains threshold_id,
source_refs, eligible_members, members_meeting_test, member_fraction (decimal
fraction), meets_supplied_threshold, and member_results containing member_id,
distinct_qualifying_providers, meets_supplied_access_test. Any gap nulls all derived
eligibility/count/percentage/comparison values; original observations remain in
source_document. Known contract/credential exclusions and failed thresholds yield
needs-review with calculable complete data. network_adequacy_certified,
licensure_inferred_from_npi, network_changed, directory_changed remain false.
