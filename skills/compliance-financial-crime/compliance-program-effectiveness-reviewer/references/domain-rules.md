# Domain method and schema

For each supplied metric, rate = numerator/denominator only when both values are supported, nonnegative, the denominator is positive and numerator≤denominator for `proportion` metrics. Both scopes/periods must match the review. Metrics are grouped into `coverage`, `outcomes`, `quality`, `resources` or `activity`; activity never contributes favorable effectiveness evidence. Overall `evidence_incomplete` remains until the required metric universe, outcome evidence, limitations, comparability and review mandate are supported. No overall effective/ineffective legal opinion is calculated.

## Common evidence contract

Read `scripts/foundation_contract.py` for the exact common contract and [evidence contract](evidence-contract.md) for professional provenance. Every consequential input uses a claim `{value, source_refs, fact_ids}` with exact registry facts; records cannot cite an unrelated source field to establish their own status. Common validation retains stale/conflicting/missing evidence and requires detached original input. Unsupported legal profiles and methods remain open.

## Native payload

`review`: `{scope, period_start, period_end, mandate_fact, independence_fact}`. `measurement_plan`: `{required_metric_ids, acceptance_fact, definition_fact}`. `metrics`: nonempty `{id, dimension, kind, scope, period_start, period_end, numerator_fact, denominator_fact, definition_fact, limitations_fact, comparable_fact}`. `outcome_evidence_fact` and `resources_evidence_fact` are required references; an `unknown` fact is permitted and remains unresolved.

The fixture in `evals/files/input.json` is de-identified synthetic supplied policy and illustrative evidence. It does not assert a real institution, live rule, independently tested control or actual legal acceptance. The native result retains detached claim-path/source/fact locators and consistency states; these locators do not establish semantic truth or automatic conclusion support. Domain findings preserve their open issues.

## Practitioner questions

Which entity, activity, population and date does each finding concern? Who owns the extracted source text and contested interpretation? What material evidence is missing or conflicting? Which conclusion is a fact, supplied institutional policy, method assumption or recommendation? What adjacent specialist must review before this artifact can be relied upon?

`definition_fact.value` for each metric exactly equals its id/dimension/kind/scope/period_start/period_end object. Measurement-plan `definition_fact.value` exactly equals `{required_metric_ids}`; its acceptance fact cannot silently support a changed measurement universe. Ratios report supplied values and no prescriptive overall effectiveness threshold.
