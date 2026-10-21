# Walk-forward research evidence contract

Select `extension: walk-forward`. This reviews supplied observations and search/protocol evidence; it does not run a strategy or infer statistical significance.

## Required evidence

Provide `protocol_source_ref`, `universe_source_ref`, pinned `strategy_version`, `protocol_version`, `data_snapshot`, `execution_model_version`, positive integer `predeclared_trial_limit`, nonnegative integer `embargo_days`, unique `trials_considered`, recorded `selected_trial_id` and explicit `universe_inventory_complete`. Also require actual `protocol_frozen_on` and `selection_decided_on`, both sourced by `protocol_source_ref` and strictly before the earliest test window. A late protocol or trial selection withholds aggregate results.

`universe` contains unique `id`, `source_ref`, `eligible_from`, inclusive `eligible_to` or null. Keep historical/delisted constituents. Each observation's `universe_ids` must exactly match eligible constituents at its observation date. A declaration of completeness is not independently authenticated.

`folds` contain unique `id`, `source_ref`, `test_start`, `test_end`, and disjoint complete `train_ids`/`test_ids`. Test windows cannot overlap. `samples` contain unique `id`, `fold_id`, `segment: train|test`, source-bound `event_id`, `observed_on`, `label_end`, `features_available_on`, `data_snapshot`, `universe_ids`, `source_ref`. Every train and test sample must repeat `strategy_version`, `protocol_version`, `execution_model_version` and `selected_trial_id` exactly matching the top-level pins; missing/mismatched pins reject. Feature availability must not follow observation. Training label end plus the embargo must precede test start. Reusing a test event across test observations or in its own fold's training is rejected. A prior test event can become training evidence for a later fold after purging; that does not prove semantic independence.

Test samples additionally require `return_unit: decimal`, `turnover_basis: one-way-notional-over-nav`, `gross_return`, nonnegative `turnover`, `cost_bps`, `borrow_cost_return`, `funding_cost_return`. Costs are return contributions: `net=gross-turnover*cost_bps/10000-borrow-funding`. Nonoverlapping return horizons are required before geometric compounding; gaps represent only supplied observations and do not imply a continuous live account path. Returns below -100% are unsupported.

## Results and stop conditions

Results retain observation costs and per-fold issues. Leakage, historical-universe gaps or trial-budget exceptions withhold the global compounded result; fold-local problems also withhold that fold's aggregate. Structural ambiguity, absent sources, duplicate economic events, overlapping test windows/horizons or incompatible units reject the input. No PBO, deflated Sharpe, significance, causality, capacity or deployment authorization is produced.

The synthetic example independently checks net returns .0085, -.0201 and .03; their product gives .0178760245. The first fold returns -.01177085. Tests introduce lookahead, survivorship, embargo, event overlap and missing-population cases.

## Primary reference

[Bailey et al., The Probability of Backtest Overfitting](https://www.davidhbailey.com/dhbpapers/backtest-prob.pdf), reviewed 2026-10-04, motivates preserving trial selection and out-of-sample limitations. Its statistical method is not implemented here. An approved independent inference engine and practitioner review are required for that claim.

## Common envelope and execution boundary

All examples are synthetic and do not establish source truth. Use the common foundation header: `request_id`, `object_id`, `as_of`, `knowledge_cutoff`, `currency`, `audience`, explicit `sources[{source_ref,version,as_of,known_at,locator}]`, and `unresolved_issues`. Dates are ISO calendar dates. Financial numbers are exact decimal strings or integers, never implicit percentages. All referenced evidence must be registered and known by the cutoff. Run the existing input, calculation and detached-input output validators; without an extension the original schema remains available. Unknown extensions fail.

A successful check yields a draft with no execution or external delivery. Retain every unresolved issue. Hashes bind supplied content; they cannot authenticate data, licenses, approval, legal applicability or independent professional acceptance.
