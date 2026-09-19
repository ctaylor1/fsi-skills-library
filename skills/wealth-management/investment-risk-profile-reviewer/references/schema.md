# JSON contract — investment risk profile v0.1

See `evals/files/request_example.json`. Common envelope: schema_version wealth-p0-v1,
request_id, household_id, as_of YYYY-MM-DD, engagement {capacity: advisory|brokerage|private-bank|trust,
jurisdiction: US}, and sources [{source_id, reference, owner, as_of, valid_until}]. Source IDs must be
unique and request.as_of within their validity dates. All numbers are finite JSON numbers, not strings
or booleans. Negative amounts/months are rejected; willingness percentage is between 0 and 100.

Domain `profile_id` is a nonempty string. `dimensions` is an object with the following named objects;
missing dimensions/fields are valid incomplete data, not permission to create values. Every dimension
requires recorded_by, recorded_on no later than review, and nonempty source_ids.

| Dimension | Additional facts |
| --- | --- |
| willingness | maximum_loss_pct; assessment_id; method_id; method_version; respondent_id; method_approval {owner, reference, source_ids} |
| loss_capacity | investable_assets; assessed_loss_capacity_amount; currency; assessment_reference; basis |
| liquidity | available_liquid_amount; required_amount; required_within_months; currency |
| horizon | months; goal_id |
| experience | items [{instrument_type, level: none|limited|experienced, source_ids}] |
| constraints | items [{constraint_id, description, source_ids}]; none_identified boolean |

Items must have unique instrument_type/constraint_id. Empty constraints require explicit
none_identified=true; it cannot coexist with listed constraints. Empty experience remains unresolved.
Currency is a three-letter uppercase code; the script does not verify market/reference-data existence.

Optional proposed_exposure: {currency, scenario_loss_amount, lockup_months, instrument_types: [string],
source_ids}. It is the caller's cited scenario/product terms, not a forecast or recommendation.

Output result: structured input_snapshot; exactly six dimensions with status recorded/incomplete/missing
and preserved facts; metrics {capacity_loss_pct, willingness_loss_amount, liquidity_shortfall};
assigned_risk_rating null; rating_decision not-made; scope. The common artifact is internal,
not-delivered, human-review-required and action_taken=false. Any finding forces needs-data.
Output validation recomputes everything from the snapshot and verifies the full artifact and digest.
