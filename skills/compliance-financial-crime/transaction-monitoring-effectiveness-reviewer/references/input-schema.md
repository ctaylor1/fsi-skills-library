# Native input schema — transaction_monitoring_effectiveness_review

The native input contains exactly `request_id`, `object_id`, `object_type`, `as_of`, `knowledge_cutoff`, `workflow`, `sources` and `data`. Use real YYYY-MM-DD dates; knowledge cutoff cannot exceed assessment date. The complete workflow/source registry follows [Foundation 2.0](foundation-contract.md). Every listed domain field is required structurally and is an exact claim `{value, source_refs, fact_ids}`; `value: null` is a valid substantive unknown. Plain text "unknown" resolves as unknown. Unknowns retain source/issue evidence; malformed claims stop intake. No undeclared data fields are permitted.

Use the synthetic `evals/files/input_complete.json` as a shape example only; do not reuse its facts, thresholds, permissions or source identities in operational work. `input_partial.json` illustrates retained unknowns, and `input_bad.json` illustrates rejected duplicate intake.

## scope object

`review_id`, `scenario_id`, `scenario_version`, `engine_id`, `engine_version`, `population_id`, `population_unit`, `population_definition`, `population_ids`, `window_from`, `window_to`, `cohort`, `expected_count`, `received_count`, `extract_complete`, `reconciliation_reference`, `data_available_through`, `freshness_criterion`, `freshness_met`, `mapping_dataset_id`, `identifier_namespace`, `entity_mapping_ref`, `entity_mapping_version`, `ambiguous_link_count`, `conflicting_link_count`, `graph_reference`, `graph_version`, `identity_limitations`.

## selection object

`sample_ids`, `sampling_method`, `selection_frame_reference`, `selection_limitations`, `label_definition`, `label_reference_domain`, `label_reference_version`, `label_acceptance_reference`, `label_owner`, `label_limitations`, `independent_assessment`, `operational_involvement`, `conflict_review`, `reporting_line_review`, `independence_review_reference`, `leakage_assessed`, `leakage_free`, `training_item_ids`.

## criteria object

`minimum_precision`, `minimum_recall`, `unit`, `owner`, `review_reference`, `basis`.

## operations object

`scenario_id`, `scenario_version`, `population_id`, `cohort`, `window_from`, `window_to`, `completed_reviews`, `analyst_minutes`, `total_cost`, `currency`, `cost_accounting`, `outcomes_reference`, `cost_limitations`.

## observations collection

Each record has a unique nonempty plain `observation_id` and these claimed fields: `item_id`, `scenario_id`, `scenario_version`, `engine_id`, `engine_version`, `population_id`, `cohort`, `event_on`, `observed_on`, `detected`, `engine_observation_reference`, `label`, `label_reference_domain`, `label_reference_version`, `label_record_reference`, `label_reviewed`.

## benchmark_references collection

Each record has a unique nonempty plain `benchmark_reference_id` and these claimed fields: `reference_domain`, `reference_version`, `context`, `claim`, `limitation`.

## technology_requirements collection

Each record has a unique nonempty plain `technology_requirement_id` and these claimed fields: `kind`, `profile_id`, `profile_version`, `requirement`, `owner`, `review_reference`, `requirement_supported`, `limitation`.

## Types and semantic scope

Boolean fields require true/false/null, counts require nonnegative integer/null and identity lists require distinct nonempty string identities (the list itself may be empty when explicitly unmeasured). Precision-bound amount/window/criterion inputs require plain nonnegative exact decimal strings such as `"1000.00000000000000001"`; fractional JSON numbers, booleans, exponent strings, NaN/Infinity and coercions are rejected. Criteria use fraction units zero through one. Currency and gross/net accounting remain explicit; no conversion is provided.

`population_unit` is economic-event, transaction, account or customer. Source system/engine/mapping/graph/reference versions, dataset IDs, namespaces, observed event/reference identities and window/cohort all retain their exact scope. Placeholder source labels do not prove facts or access. Benchmark references have their own domain/context/limits and are not engine observations. Technology requirement kinds are engine, vendor, model, copilot, real-time or graph. The executable predicates in local `scripts/domain.py` define precise supported enums; domain rules describe dependent withholding.
