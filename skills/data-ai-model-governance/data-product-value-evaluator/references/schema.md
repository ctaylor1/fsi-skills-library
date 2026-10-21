# Native schema

Required top-level keys: case_id (durable nonempty text), as_of (YYYY-MM-DD), context {capacity,represented_party,object_id,jurisdiction,line_of_business}, sources [{source_ref,version,as_of, optional locator}], unresolved_issues (explicit list of open questions), data (object). Source IDs are unique; every source date is known and no later than as_of. Unknown context is explicit unknown, which keeps outputs partial.

All data fields below are required unless explicitly marked optional in the method. Inventories are explicit arrays of objects with unique nonblank IDs; a missing/null inventory is unknown, never confirmed empty. Null numeric values preserve missingness. Numeric inputs allow finite decimal strings/numbers, never booleans/NaN/infinity; nonnegative unless the method permits signed values. Probabilities/fractions are in [0,1], counts/attempts/waves are integral. All source_refs arrays must identify supplied versioned records.

The review profile is nested at **data.profile** (not top level). Required profile keys: profile_id, version, reviewed_by, source_refs, jurisdictions and lines_of_business (explicit arrays containing context), effective_from/effective_to inclusive around as_of, and method exactly `paired-data-product-value-v1`. A supplied profile is not authenticated approval.

## Data fields

| Field | Shape |
| --- | --- |
| `data.purpose` | text or null |
| `data.population` | text or null |
| `data.outcome_definition` | text or null |
| `data.currency` | text or null |
| `data.baseline_version` | text or null |
| `data.augmented_version` | text or null |
| `data.comparison_protocol` | text or null |
| `data.paired_inventory_complete` | boolean |
| `data.ground_truth_reviewed` | boolean |
| `data.license` | object |
| `data.license.provider` | text or null |
| `data.license.version` | text or null |
| `data.license.purpose` | text or null |
| `data.license.reviewed_by` | text or null |
| `data.license.retention_rule` | text or null |
| `data.license.use_permitted` | boolean |
| `data.license.effective_from` | calendar date or null |
| `data.license.effective_to` | calendar date or null |
| `data.license.source_refs` | explicit array of unique strings |
| `data.cases` | array of objects |
| `data.cases[].case_id` | text or null |
| `data.cases[].decision_on` | calendar date or null |
| `data.cases[].outcome_on` | calendar date or null |
| `data.cases[].provider_available_on` | calendar date or null |
| `data.cases[].population` | text or null |
| `data.cases[].currency` | text or null |
| `data.cases[].baseline_version` | text or null |
| `data.cases[].augmented_version` | text or null |
| `data.cases[].provider_match` | boolean |
| `data.cases[].truth` | boolean |
| `data.cases[].baseline_prediction` | boolean |
| `data.cases[].augmented_prediction` | boolean |
| `data.cases[].baseline_outcome_cost` | finite number or null |
| `data.cases[].augmented_outcome_cost` | finite number or null |
| `data.cases[].source_refs` | explicit array of unique strings |
| `data.projection` | object |
| `data.projection.representativeness_reviewed` | boolean |
| `data.projection.basis` | text or null |
| `data.projection.reviewed_by` | text or null |
| `data.projection.annual_volume` | finite number or null |
| `data.projection.annual_license_cost` | finite number or null |
| `data.projection.incremental_cost_per_case` | finite number or null |
| `data.projection.annual_operating_cost` | finite number or null |
| `data.projection.currency` | text or null |
| `data.projection.source_refs` | explicit array of unique strings |

## Exact enums and semantic requirements

The supported method is `paired-data-product-value-v1`. License fields bind provider/version/purpose and effective dates; these supplied assertions must be independently authorized for real use. All original cases, including unmatched provider records, remain in the paired benchmark. A matched record must have been available no later than its decision date; known reviewed outcomes mature between decision and review. Predictions and truth are explicit booleans, never null-as-negative. Compare fixed declared baseline/augmented versions and population. Confusion counts use true/false positives/negatives; precision=TP/(TP+FP), recall=TP/(TP+FN), zero denominators return null. Observed cost reduction sums baseline_outcome_cost minus augmented_outcome_cost over all paired cases; no invented costs for errors. Coverage is matched count / full sample size. An optional separately reviewed representative projection uses annual_volume * (sample_mean_reduction - incremental_cost_per_case) - annual_license_cost - annual_operating_cost. Outcomes must exclude those separately subtracted costs. No projection when representativeness or other inputs are unresolved; no causal attribution, significance, discrimination/fairness acceptance or vendor selection. An unmatched case still needs an explicitly supplied augmented/fallback prediction and cost; never assume it succeeded.

Optional upstream_artifacts and context_mappings follow workflow-contract.md. All outputs retain source_document, context, findings, native results, unresolved_issues and artifact. Native results use Decimal strings; ratios are fractions except explicitly labeled minutes/hours or counts. Unknown measures are null. No action, approval or execution flags can be promoted.


## Conditional fields and exact vocabulary

data.projection is optional and may be null. Unknown projection inputs withhold the projection, while separately valid observed benchmark results remain available. provider_available_on may be null for an explicitly unmatched case; both prediction and cost fields still require explicit fallback observations.

Unclassified top-level or upstream unresolved issues conservatively withhold dependent measurements and recommendations. Keep all unresolved issues; do not remove them to obtain a complete result. Content hashes establish identity, not source authenticity.

license_usable_for_stated_purpose assesses supplied license evidence, scope and dates separately from case/projection sufficiency. It is not authentication, professional approval or proof of permitted production use.
