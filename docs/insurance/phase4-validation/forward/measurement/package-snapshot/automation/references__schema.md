# Native schema

Required top-level keys: case_id (durable nonempty text), as_of (YYYY-MM-DD), context {capacity,represented_party,object_id,jurisdiction,line_of_business}, sources [{source_ref,version,as_of, optional locator}], unresolved_issues (explicit list of open questions), data (object). Source IDs are unique; every source date is known and no later than as_of. Unknown context is explicit unknown, which keeps outputs partial.

All data fields below are required unless explicitly marked optional in the method. Inventories are explicit arrays of objects with unique nonblank IDs; a missing/null inventory is unknown, never confirmed empty. Null numeric values preserve missingness. Numeric inputs allow finite decimal strings/numbers, never booleans/NaN/infinity; nonnegative unless the method permits signed values. Probabilities/fractions are in [0,1], counts/attempts/waves are integral. All source_refs arrays must identify supplied versioned records.

The review profile is nested at **data.profile** (not top level). Required profile keys: profile_id, version, reviewed_by, source_refs, jurisdictions and lines_of_business (explicit arrays containing context), effective_from/effective_to inclusive around as_of, and method exactly `paired-workflow-automation-v1`. A supplied profile is not authenticated approval.

## Data fields

| Field | Shape |
| --- | --- |
| `data.population` | text or null |
| `data.comparison_protocol` | text or null |
| `data.owner` | text or null |
| `data.currency` | text or null |
| `data.workflow_version` | text or null |
| `data.paired_inventory_complete` | boolean |
| `data.measurement_protocol_reviewed` | boolean |
| `data.comparison_type` | text or null |
| `data.requested_mode` | text or null |
| `data.maximum_candidate_error_rate` | finite number or null |
| `data.cases` | array of objects |
| `data.cases[].case_id` | text or null |
| `data.cases[].workflow_version` | text or null |
| `data.cases[].population` | text or null |
| `data.cases[].observed_on` | calendar date or null |
| `data.cases[].currency` | text or null |
| `data.cases[].baseline_human_minutes` | finite number or null |
| `data.cases[].candidate_human_minutes` | finite number or null |
| `data.cases[].baseline_nonlabor_cost` | finite number or null |
| `data.cases[].candidate_nonlabor_cost` | finite number or null |
| `data.cases[].baseline_elapsed_seconds` | finite number or null |
| `data.cases[].candidate_elapsed_seconds` | finite number or null |
| `data.cases[].baseline_error` | boolean |
| `data.cases[].candidate_error` | boolean |
| `data.cases[].source_refs` | explicit array of unique strings |
| `data.scenarios` | array of objects |
| `data.scenarios[].scenario_id` | text or null |
| `data.scenarios[].annual_volume` | finite number or null |
| `data.scenarios[].eligible_fraction` | finite number or null |
| `data.scenarios[].hourly_labor_cost` | finite number or null |
| `data.scenarios[].cash_realization_fraction` | finite number or null |
| `data.scenarios[].annual_fixed_cost` | finite number or null |
| `data.scenarios[].implementation_cost` | finite number or null |
| `data.scenarios[].currency` | text or null |
| `data.scenarios[].source_refs` | explicit array of unique strings |
| `data.controls` | array of objects |
| `data.controls[].control_id` | text or null |
| `data.controls[].owner` | text or null |
| `data.controls[].test` | text or null |
| `data.controls[].actual` | text or null |
| `data.controls[].status` | text or null |
| `data.controls[].source_refs` | explicit array of unique strings |

## Exact enums and semantic requirements

The supported method is `paired-workflow-automation-v1`; comparison_type must be paired-same-cases. Each case has matched baseline/candidate human minutes, nonlabor cost, elapsed seconds and independently reviewed boolean error labels, under identical population/workflow version/currency. Candidate human work includes review, exceptions and rework; nonlabor costs exclude that labor to prevent double counting. Means use the complete paired population, not only successes. Saved minutes = baseline minus candidate. Per scenario eligible annual volume = annual_volume * eligible_fraction; signed capacity hours = volume * saved_minutes / 60; capacity value = hours * hourly_labor_cost. Annual cash net = capacity_value * explicit cash_realization_fraction + volume * (baseline_nonlabor_cost - candidate_nonlabor_cost) - annual_fixed_cost. The realization fraction is a scenario assumption applying to signed capacity change, not proof of headcount savings. Simple undiscounted payback months = implementation_cost / positive annual_cash_net * 12; otherwise null. No causal effect, confidence interval, tax/discounting or benefits realization is inferred. A pilot candidate requires known measurements, error rate at/below supplied maximum, all required control tests passed and positive net in at least one disclosed scenario. Autonomous regulated decisions are outside support; a positive projection cannot override controls. Scenarios are projections, never observed savings.

Optional upstream_artifacts and context_mappings follow workflow-contract.md. All outputs retain source_document, context, findings, native results, unresolved_issues and artifact. Native results use Decimal strings; ratios are fractions except explicitly labeled minutes/hours or counts. Unknown measures are null. No action, approval or execution flags can be promoted.


## Conditional fields and exact vocabulary

Exact requested_mode values: assist, draft, deterministic-automation, autonomous-regulated-decision. Required controls[].control_id values: human-review, privacy, permission-scope, failure-recovery, auditability, evaluation-quality. All six are required, with status passed/failed/not-run. Additional distinct control IDs may be supplied.

Unclassified top-level or upstream unresolved issues conservatively withhold dependent measurements and recommendations. Keep all unresolved issues; do not remove them to obtain a complete result. Content hashes establish identity, not source authenticity.
