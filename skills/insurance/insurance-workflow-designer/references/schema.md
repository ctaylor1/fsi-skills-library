# Native schema

Required top-level keys: case_id (durable nonempty text), as_of (YYYY-MM-DD), context {capacity,represented_party,object_id,jurisdiction,line_of_business}, sources [{source_ref,version,as_of, optional locator}], unresolved_issues (explicit list of open questions), data (object). Source IDs are unique; every source date is known and no later than as_of. Unknown context is explicit unknown, which keeps outputs partial.

All data fields below are required unless explicitly marked optional in the method. Inventories are explicit arrays of objects with unique nonblank IDs; a missing/null inventory is unknown, never confirmed empty. Null numeric values preserve missingness. Numeric inputs allow finite decimal strings/numbers, never booleans/NaN/infinity; nonnegative unless the method permits signed values. Probabilities/fractions are in [0,1], counts/attempts/waves are integral. All source_refs arrays must identify supplied versioned records.

The review profile is nested at **data.profile** (not top level). Required profile keys: profile_id, version, reviewed_by, source_refs, jurisdictions and lines_of_business (explicit arrays containing context), effective_from/effective_to inclusive around as_of, and method exactly `reviewed-insurance-paths-v1`. A supplied profile is not authenticated approval.

## Data fields

| Field | Shape |
| --- | --- |
| `data.business_outcome` | text or null |
| `data.population_basis` | text or null |
| `data.path_inventory_complete` | boolean |
| `data.source_contracts` | array of objects |
| `data.source_contracts[].contract_id` | text or null |
| `data.source_contracts[].system` | text or null |
| `data.source_contracts[].version` | text or null |
| `data.source_contracts[].owner` | text or null |
| `data.source_contracts[].access_scope` | text or null |
| `data.source_contracts[].purpose` | text or null |
| `data.source_contracts[].schema_version` | text or null |
| `data.source_contracts[].freshness_rule` | text or null |
| `data.source_contracts[].access_reviewed` | boolean |
| `data.source_contracts[].purpose_reviewed` | boolean |
| `data.source_contracts[].source_refs` | explicit array of unique strings |
| `data.steps` | array of objects |
| `data.steps[].step_id` | text or null |
| `data.steps[].mode` | text or null |
| `data.steps[].owner` | text or null |
| `data.steps[].input_contract` | text or null |
| `data.steps[].output_contract` | text or null |
| `data.steps[].completion_evidence` | text or null |
| `data.steps[].contract_ids` | explicit array of unique strings |
| `data.steps[].human_minutes` | finite number or null |
| `data.steps[].elapsed_minutes` | finite number or null |
| `data.steps[].source_refs` | explicit array of unique strings |
| `data.steps[].failure_step` | text or null |
| `data.steps[].timeout_rule` | text or null |
| `data.steps[].audit_record` | text or null |
| `data.steps[].max_attempts` | finite number or null |
| `data.paths` | array of objects |
| `data.paths[].path_id` | text or null |
| `data.paths[].design` | text or null |
| `data.paths[].kind` | text or null |
| `data.paths[].outcome` | text or null |
| `data.paths[].population_basis` | text or null |
| `data.paths[].step_ids` | explicit array of unique strings |
| `data.paths[].share` | finite number or null |
| `data.paths[].failure_of` | explicit array of unique strings |
| `data.paths[].source_refs` | explicit array of unique strings |

## Exact enums and semantic requirements

The supported method is `reviewed-insurance-paths-v1`. Every explicit serial path lists unique step IDs; repeated work needs separately identified bounded steps. Add human minutes and elapsed minutes within a path, then weight by supplied shares separately for current and target. These are scenario assumptions, not measured process improvement or critical-path scheduling. Shares must total exactly one for each design and describe the same complete, mutually exclusive population. Each design has a normal/exception classification; explicit zero probability is allowed. Every used machine step must have a corresponding exception path naming it in failure_of and including its human fallback. Step mode is human/read/draft/proposed-write; machine attempts are integers 1..10. Proposed writes require owner approval, an idempotency key, receipt check and recovery plan. No step is executed. Source contracts preserve reviewed purpose/access/schema/freshness assumptions; production access and connector conformance remain unverified. A gap withholds path arithmetic while preserving the proposed design.

Optional upstream_artifacts and context_mappings follow workflow-contract.md. All outputs retain source_document, context, findings, native results, unresolved_issues and artifact. Native results use Decimal strings; ratios are fractions except explicitly labeled minutes/hours or counts. Unknown measures are null. No action, approval or execution flags can be promoted.


## Conditional fields and exact vocabulary

Conditional step fields timeout_rule, audit_record, max_attempts and failure_step are required for read/draft/proposed-write steps. Human steps need none of those machine-only fields. Proposed-write additionally requires approval_owner, idempotency_key, receipt_check and recovery_plan. failure_of is an explicit array on every path, empty on a normal path.

Unclassified top-level or upstream unresolved issues conservatively withhold dependent measurements and recommendations. Keep all unresolved issues; do not remove them to obtain a complete result. Content hashes establish identity, not source authenticity.
