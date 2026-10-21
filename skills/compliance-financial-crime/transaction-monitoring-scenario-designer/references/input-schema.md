# Native input schema — transaction_monitoring_scenario_design

The native input contains exactly `request_id`, `object_id`, `object_type`, `as_of`, `knowledge_cutoff`, `workflow`, `sources` and `data`. Use real YYYY-MM-DD dates; knowledge cutoff cannot exceed assessment date. The complete workflow/source registry follows [Foundation 2.0](foundation-contract.md). Every listed domain field is required structurally and is an exact claim `{value, source_refs, fact_ids}`; `value: null` is a valid substantive unknown. Plain text "unknown" resolves as unknown. Unknowns retain source/issue evidence; malformed claims stop intake. No undeclared data fields are permitted.

Use the synthetic `evals/files/input_complete.json` as a shape example only; do not reuse its facts, thresholds, permissions or source identities in operational work. `input_partial.json` illustrates retained unknowns, and `input_bad.json` illustrates rejected duplicate intake.

## scenario object

`scenario_id`, `design_version`, `risk_id`, `risk_hypothesis`, `typology`, `target_behavior`, `population_id`, `population_unit`, `eligibility_definition`, `engine_id`, `engine_version`, `processing_mode`, `logic_spec`, `window_value`, `window_unit`, `entity_mapping_ref`, `entity_mapping_version`, `mapping_dataset_id`, `identifier_namespace`, `ambiguous_link_count`, `conflicting_link_count`, `mapping_method`, `identity_limitations`, `graph_reference`, `graph_version`, `currency`, `amount_accounting`.

## evaluation object

`backtest_dataset_id`, `backtest_from`, `backtest_to`, `holdout_dataset_id`, `holdout_from`, `holdout_to`, `training_item_ids`, `holdout_item_ids`, `sampling_method`, `label_definition`, `label_reference`, `label_limitations`, `leakage_assessed`, `holdout_independent`, `bias_dimensions`, `metric_definitions`, `acceptance_criteria`, `criteria_owner`, `criteria_review_reference`, `evaluation_limitations`.

## change object

`change_id`, `prior_configuration_ref`, `proposed_configuration_ref`, `owner`, `approver_role`, `planned_start`, `shadow_mode_plan`, `reconciliation_gate`, `rollback_trigger`, `rollback_configuration_ref`, `rollback_owner`, `review_cadence`.

## parameters collection

Each record has a unique nonempty plain `parameter_id` and these claimed fields: `name`, `value`, `unit`, `currency`, `rationale`.

## data_requirements collection

Each record has a unique nonempty plain `requirement_id` and these claimed fields: `field`, `source_system`, `source_version`, `lineage_reference`, `transformation`, `null_handling`, `data_owner`, `event_identity_rule`, `reconciliation_definition`, `expected_count`, `loaded_count`, `expected_total`, `loaded_total`, `currency`, `amount_accounting`, `data_available_through`, `freshness_criterion`, `freshness_met`.

## technology_requirements collection

Each record has a unique nonempty plain `technology_requirement_id` and these claimed fields: `kind`, `profile_id`, `profile_version`, `requirement`, `owner`, `review_reference`, `requirement_supported`, `limitation`.

## engine_observations collection

Each record has a unique nonempty plain `engine_observation_id` and these claimed fields: `engine_id`, `engine_version`, `scenario_id`, `scenario_version`, `observation`, `observed_on`, `population_id`.

## benchmark_references collection

Each record has a unique nonempty plain `benchmark_reference_id` and these claimed fields: `reference_domain`, `reference_version`, `context`, `claim`, `limitation`.

## Types and semantic scope

Boolean fields require true/false/null, counts require nonnegative integer/null and identity lists require distinct nonempty string identities (the list itself may be empty when explicitly unmeasured). Precision-bound amount/window/criterion inputs require plain nonnegative exact decimal strings such as `"1000.00000000000000001"`; fractional JSON numbers, booleans, exponent strings, NaN/Infinity and coercions are rejected. Criteria use fraction units zero through one. Currency and gross/net accounting remain explicit; no conversion is provided.

`population_unit` is economic-event, transaction, account or customer. Source system/engine/mapping/graph/reference versions, dataset IDs, namespaces, observed event/reference identities and window/cohort all retain their exact scope. Placeholder source labels do not prove facts or access. Benchmark references have their own domain/context/limits and are not engine observations. Technology requirement kinds are engine, vendor, model, copilot, real-time or graph. The executable predicates in local `scripts/domain.py` define precise supported enums; domain rules describe dependent withholding.
