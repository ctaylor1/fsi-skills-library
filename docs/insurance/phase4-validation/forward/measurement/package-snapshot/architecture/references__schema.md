# Native schema

Required top-level keys: case_id (durable nonempty text), as_of (YYYY-MM-DD), context {capacity,represented_party,object_id,jurisdiction,line_of_business}, sources [{source_ref,version,as_of, optional locator}], unresolved_issues (explicit list of open questions), data (object). Source IDs are unique; every source date is known and no later than as_of. Unknown context is explicit unknown, which keeps outputs partial.

All data fields below are required unless explicitly marked optional in the method. Inventories are explicit arrays of objects with unique nonblank IDs; a missing/null inventory is unknown, never confirmed empty. Null numeric values preserve missingness. Numeric inputs allow finite decimal strings/numbers, never booleans/NaN/infinity; nonnegative unless the method permits signed values. Probabilities/fractions are in [0,1], counts/attempts/waves are integral. All source_refs arrays must identify supplied versioned records.

The review profile is nested at **data.profile** (not top level). Required profile keys: profile_id, version, reviewed_by, source_refs, jurisdictions and lines_of_business (explicit arrays containing context), effective_from/effective_to inclusive around as_of, and method exactly `component-interface-requirements-v1`. A supplied profile is not authenticated approval.

## Data fields

| Field | Shape |
| --- | --- |
| `data.business_outcome` | text or null |
| `data.owner` | text or null |
| `data.currency` | text or null |
| `data.cost_period` | text or null |
| `data.scope` | text or null |
| `data.inventory_complete` | boolean |
| `data.components` | array of objects |
| `data.components[].component_id` | text or null |
| `data.components[].responsibility` | text or null |
| `data.components[].owner` | text or null |
| `data.components[].technology_choice` | text or null |
| `data.components[].alternative` | text or null |
| `data.components[].tradeoff` | text or null |
| `data.components[].failure_domain` | text or null |
| `data.components[].data_classification` | text or null |
| `data.components[].retention_rule` | text or null |
| `data.components[].recovery_runbook` | text or null |
| `data.components[].currency` | text or null |
| `data.components[].cost_period` | text or null |
| `data.components[].cost` | finite number or null |
| `data.components[].source_refs` | explicit array of unique strings |
| `data.interfaces` | array of objects |
| `data.interfaces[].interface_id` | text or null |
| `data.interfaces[].from_component` | text or null |
| `data.interfaces[].to_component` | text or null |
| `data.interfaces[].contract_version` | text or null |
| `data.interfaces[].payload_schema` | text or null |
| `data.interfaces[].purpose` | text or null |
| `data.interfaces[].authentication` | text or null |
| `data.interfaces[].authorization_scope` | text or null |
| `data.interfaces[].encryption` | text or null |
| `data.interfaces[].timeout` | text or null |
| `data.interfaces[].failure_route` | text or null |
| `data.interfaces[].trace_id` | text or null |
| `data.interfaces[].delivery` | text or null |
| `data.interfaces[].operation` | text or null |
| `data.interfaces[].purpose_reviewed` | boolean |
| `data.interfaces[].max_attempts` | finite number or null |
| `data.interfaces[].idempotency_key` | text or null |
| `data.interfaces[].approval_owner` | text or null |
| `data.interfaces[].receipt_check` | text or null |
| `data.interfaces[].recovery_plan` | text or null |
| `data.interfaces[].source_refs` | explicit array of unique strings |
| `data.requirements` | array of objects |
| `data.requirements[].requirement_id` | text or null |
| `data.requirements[].component_id` | text or null |
| `data.requirements[].metric` | text or null |
| `data.requirements[].unit` | text or null |
| `data.requirements[].owner` | text or null |
| `data.requirements[].workload_profile` | text or null |
| `data.requirements[].operator` | text or null |
| `data.requirements[].threshold` | finite number or null |
| `data.requirements[].source_refs` | explicit array of unique strings |
| `data.measurements` | array of objects |
| `data.measurements[].requirement_id` | text or null |
| `data.measurements[].component_id` | text or null |
| `data.measurements[].metric` | text or null |
| `data.measurements[].unit` | text or null |
| `data.measurements[].workload_profile` | text or null |
| `data.measurements[].observed_on` | calendar date or null |
| `data.measurements[].value` | finite number or null |
| `data.measurements[].source_refs` | explicit array of unique strings |

## Exact enums and semantic requirements

The supported method is `component-interface-requirements-v1`. Produce a named component/responsibility/failure-domain design, interfaces and tradeoffs against supplied alternatives. Interfaces reference actual components; synchronous, at-least-once and at-most-once delivery are supported. Duplicate logical endpoint/version flows are rejected as gaps. Proposed writes require idempotency, human approval owner, receipt and recovery contracts; no execution occurs. Requirements bind component, metric, unit and workload profile. Compare observed values with an explicit <= or >= threshold only when measurement scope/date matches exactly. No interpolation, extrapolation, inferred availability, summed percentile latency or invented capacity is performed. Sum complete same-currency/same-period component costs; any evidence/scope gap withholds measured fit and total cost. Actual failure-domain independence and provider security/conformance require separate acceptance.

Optional upstream_artifacts and context_mappings follow workflow-contract.md. All outputs retain source_document, context, findings, native results, unresolved_issues and artifact. Native results use Decimal strings; ratios are fractions except explicitly labeled minutes/hours or counts. Unknown measures are null. No action, approval or execution flags can be promoted.


## Conditional fields and exact vocabulary

Exact interfaces[].operation values: read or proposed-write. Proposed-write requires idempotency_key, approval_owner, receipt_check and recovery_plan. Delivery is synchronous, at-least-once or at-most-once.

Unclassified top-level or upstream unresolved issues conservatively withhold dependent measurements and recommendations. Keep all unresolved issues; do not remove them to obtain a complete result. Content hashes establish identity, not source authenticity.
