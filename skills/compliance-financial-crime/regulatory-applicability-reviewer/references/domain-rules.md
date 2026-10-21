# Domain method and schema

Supported rule method is `explicit-comparisons-v1`: `all`/`any` over `eq`, `in`, `gte`, `lte`, `contains`, with tri-state propagation. A rule is evaluated only with a supported completeness fact and confirmed rule lifecycle/status/effective evidence. Supplied exclusions are additional criteria; a true exclusion supports `not_applicable` only when the rule/exclusion method is complete. Proposed/adopted/stayed/withdrawn/superseded rules retain computed perimeter indicators but do not become currently binding. Permissions are separate fact-backed observations, not an authorization decision.

## Common evidence contract

Read `scripts/foundation_contract.py` for the exact common contract and [evidence contract](evidence-contract.md) for professional provenance. Every consequential input uses a claim `{value, source_refs, fact_ids}` with exact registry facts; records cannot cite an unrelated source field to establish their own status. Common validation retains stale/conflicting/missing evidence and requires detached original input. Unsupported legal profiles and methods remain open.

## Native payload

`entities`: nonempty `{id, facts: {dimension: claim}, permissions_fact}`. `rules`: nonempty `{id, authority_fact, lifecycle_fact, effective_date_fact, compliance_date_fact, completeness_fact, profile_fact, method, operator, criteria: [{dimension, comparator, expected, rule_fact}], exclusions: [...], required_permissions}`. Missing facts yield unknown; malformed rule methods/operators are rejected or declared unsupported rather than interpreted silently.

The fixture in `evals/files/input.json` is de-identified synthetic supplied policy and illustrative evidence. It does not assert a real institution, live rule, independently tested control or actual legal acceptance. The native result retains detached claim-path/source/fact locators and consistency states; these locators do not establish semantic truth or automatic conclusion support. Domain findings preserve their open issues.

## Practitioner questions

Which entity, activity, population and date does each finding concern? Who owns the extracted source text and contested interpretation? What material evidence is missing or conflicting? Which conclusion is a fact, supplied institutional policy, method assumption or recommendation? What adjacent specialist must review before this artifact can be relied upon?

`profile_fact.value` must exactly equal `{rule_id, method, operator, criteria: [{dimension, comparator, expected}], exclusions: [...], required_permissions}`. Criterion `rule_fact.value` exactly equals its dimension/comparator/expected object. Exact JSON comparisons keep booleans distinct from numbers.
