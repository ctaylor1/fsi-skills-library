# Native schema

Required top-level keys: case_id (durable nonempty text), as_of (YYYY-MM-DD), context {capacity,represented_party,object_id,jurisdiction,line_of_business}, sources [{source_ref,version,as_of, optional locator}], unresolved_issues (explicit list of open questions), data (object). Source IDs are unique; every source date is known and no later than as_of. Unknown context is explicit unknown, which keeps outputs partial.

All data fields below are required unless explicitly marked optional in the method. Inventories are explicit arrays of objects with unique nonblank IDs; a missing/null inventory is unknown, never confirmed empty. Null numeric values preserve missingness. Numeric inputs allow finite decimal strings/numbers, never booleans/NaN/infinity; nonnegative unless the method permits signed values. Probabilities/fractions are in [0,1], counts/attempts/waves are integral. All source_refs arrays must identify supplied versioned records.

The review profile is nested at **data.profile** (not top level). Required profile keys: profile_id, version, reviewed_by, source_refs, jurisdictions and lines_of_business (explicit arrays containing context), effective_from/effective_to inclusive around as_of, and method exactly `insurance-core-option-migration-v1`. A supplied profile is not authenticated approval.

## Data fields

| Field | Shape |
| --- | --- |
| `data.currency` | text or null |
| `data.scope` | text or null |
| `data.owner` | text or null |
| `data.inventory_version` | text or null |
| `data.inventory_complete` | boolean |
| `data.requirements` | array of objects |
| `data.requirements[].requirement_id` | text or null |
| `data.requirements[].description` | text or null |
| `data.requirements[].owner` | text or null |
| `data.requirements[].mandatory` | boolean |
| `data.requirements[].source_refs` | explicit array of unique strings |
| `data.options` | array of objects |
| `data.options[].option_id` | text or null |
| `data.options[].strategy` | text or null |
| `data.options[].rationale` | text or null |
| `data.options[].history_preservation` | text or null |
| `data.options[].form_version_mapping` | text or null |
| `data.options[].policy_identity_mapping` | text or null |
| `data.options[].billing_claims_coexistence` | text or null |
| `data.options[].cost_inventory_complete` | boolean |
| `data.options[].cost_horizon` | text or null |
| `data.options[].fits` | array of objects |
| `data.options[].fits[].requirement_id` | text or null |
| `data.options[].fits[].disposition` | text or null |
| `data.options[].fits[].rationale` | text or null |
| `data.options[].fits[].source_refs` | explicit array of unique strings |
| `data.options[].costs` | array of objects |
| `data.options[].costs[].cost_id` | text or null |
| `data.options[].costs[].amount` | finite number or null |
| `data.options[].costs[].currency` | text or null |
| `data.options[].costs[].period` | text or null |
| `data.options[].costs[].basis` | text or null |
| `data.options[].costs[].source_refs` | explicit array of unique strings |
| `data.options[].source_refs` | explicit array of unique strings |
| `data.batches` | array of objects |
| `data.batches[].batch_id` | text or null |
| `data.batches[].owner` | text or null |
| `data.batches[].scope` | text or null |
| `data.batches[].mapping_version` | text or null |
| `data.batches[].source_snapshot` | text or null |
| `data.batches[].target_snapshot` | text or null |
| `data.batches[].rollback_trigger` | text or null |
| `data.batches[].rollback_owner` | text or null |
| `data.batches[].rollback_data_plan` | text or null |
| `data.batches[].rehearsal_evidence_reviewed` | boolean |
| `data.batches[].wave` | finite number or null |
| `data.batches[].depends_on` | explicit array of unique strings |
| `data.batches[].new_writes_after_cutover` | boolean |
| `data.batches[].delta_recovery_evidence` | text or null |
| `data.batches[].source_refs` | explicit array of unique strings |
| `data.reconciliations` | array of objects |
| `data.reconciliations[].control_id` | text or null |
| `data.reconciliations[].batch_id` | text or null |
| `data.reconciliations[].source_snapshot` | text or null |
| `data.reconciliations[].target_snapshot` | text or null |
| `data.reconciliations[].mapping_version` | text or null |
| `data.reconciliations[].measure` | text or null |
| `data.reconciliations[].unit` | text or null |
| `data.reconciliations[].scope` | text or null |
| `data.reconciliations[].source_value` | finite number or null |
| `data.reconciliations[].target_value` | finite number or null |
| `data.reconciliations[].tolerance` | finite number or null |
| `data.reconciliations[].source_refs` | explicit array of unique strings |
| `data.gates` | array of objects |
| `data.gates[].gate_id` | text or null |
| `data.gates[].owner` | text or null |
| `data.gates[].test` | text or null |
| `data.gates[].expected` | text or null |
| `data.gates[].actual` | text or null |
| `data.gates[].observed_on` | calendar date or null |
| `data.gates[].status` | text or null |
| `data.gates[].source_refs` | explicit array of unique strings |

## Exact enums and semantic requirements

The supported method is `insurance-core-option-migration-v1`. Requirements have explicit mandatory booleans; option fits are met/not-met/unknown with rationale. Retain/replatform/refactor/replace are supported strategies. Every requirement needs exactly one assessment per option. Costs are sums of supplied disjoint components for a declared horizon, not NPV or a ranking; compare only identical horizons and complete inventories. Migration batches form an acyclic dependency graph and dependencies occupy strictly earlier numeric waves. Source and target control snapshots and mapping versions must match the batch. Reconciliation is target minus source; compare absolute difference to an explicit nonnegative tolerance within the same measure, unit and scope. Required test IDs are reconciliation, rollback, parallel-run, security and business-acceptance. A passed supplied test is evidence to review, not independent verification. New writes after cutover require a documented delta-recovery rehearsal. No selected option or cutover authority is emitted.

Optional upstream_artifacts and context_mappings follow workflow-contract.md. All outputs retain source_document, context, findings, native results, unresolved_issues and artifact. Native results use Decimal strings; ratios are fractions except explicitly labeled minutes/hours or counts. Unknown measures are null. No action, approval or execution flags can be promoted.


## Conditional fields and exact vocabulary

Option fits[].disposition is met/not-met/unknown. gate_id must include reconciliation, rollback, parallel-run, security, business-acceptance. Gate status is passed/failed/not-run. delta_recovery_evidence is conditional on new_writes_after_cutover=true. Every control binds the scope, snapshots and mapping version of its referenced batch; program scope can contain multiple batch scopes.

Unclassified top-level or upstream unresolved issues conservatively withhold dependent measurements and recommendations. Keep all unresolved issues; do not remove them to obtain a complete result. Content hashes establish identity, not source authenticity.
