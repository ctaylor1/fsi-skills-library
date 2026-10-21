# Native input and output contract

The request uses `investment-foundation/1.0`: request_id, object_id, as_of and knowledge_cutoff (`YYYY-MM-DD`), currency, audience=`internal-review`, nonempty versioned sources and optional unresolved_issues. Each source has source_ref, version, as_of, known_at and an inspectable locator. Sources cannot be known after knowledge_cutoff; referenced sources must be eligible for the review date and audience. Additional request fields are purpose, principal, snapshot_id and owner.

All row collections below require 1–10,000 objects with a unique named ID and a registered source_ref. An empty inventory is rejected instead of being labeled complete. Unknown semantic values are explicit null, not missing or zero. Numeric values accept finite bounded decimals; use decimal strings to preserve supplied precision.

| Collection | Required content |
| --- | --- |
| datasets / dataset_id | owner, classification, retention_rule, component_id from shared architecture, license_id, grain_dimensions: unique subset of security/portfolio/account/benchmark/time_series |
| fields / field_id | dataset_id, definition, unit, currency (request currency or not-applicable), source_system, source_field, transformation, transformation_version, owner, value_type=decimal/text, nullable boolean |
| identities / identity_id | dimension, namespace, native_key. `(dimension, namespace, native_key)` is unique across IDs. |
| licenses / license_id | dataset_id, principal, license_version, contract_locator, purposes and audiences lists, effective_from/effective_to (inclusive). These are supplied declarations. |
| permission_observations / observation_id | dataset_id, principal, purpose, audience, operation=read, decision=allowed/denied/unknown, observed_on. One observation per dataset must match the request and review date for a supplied sample to be eligible. |
| history / record_id | field_id, exact dimensions map to compatible identity IDs, unit/currency matching field, explicit value, valid_from/valid_to and known_from/known_to. End dates are exclusive; null means open. |
| queries / query_id | field_id, exact dimensions, valid_on, known_on. Dates cannot exceed review/knowledge boundaries. |
| monitors / monitor_id | dataset_id, snapshot_id matching request, owner, metric, unit, operator=<=/>=, threshold, value or null, basis=observed/projected, incident_route, runbook; observed basis requires observed_on. |

History `known_from` and any closed `known_to` must be no later than the linked source's known_at, review date and knowledge_cutoff. Historical value start cannot be after review. The same source may document an export of several prior assertions; this checks chronology of its supplied claims, not historical authenticity. Queries select exact field/grain candidates whose two half-open intervals contain valid_on and known_on. Every candidate ID is retained. Zero or multiple candidates withhold the value; no automatic precedence or latest-row rule exists.

`shared_reviews.architecture` requires `{input, output, source_ref}`. Input/output use the real `solution-architecture-planner` native schema and are reconstructed by its pinned implementation. `input.context.object_id`, `input.as_of` and `input.data.currency` must match AM context exactly. Every native shared source must exist in the AM registry with identical version/as_of; outer source_ref binds the received review. Optional `shared_reviews.data_value` uses the same pair structure for `data-product-value-evaluator`; its native `data.purpose` must also equal the AM purpose.

Output is a detached foundation artifact. Results include semantic and identity contracts, access_evidence, resolved_sample, observability, and summaries of the validated shared outputs. It retains source references, exact sample record IDs, units and dates. `source_authentication`, `permission_verified`, `deployment_authorized` and `production_identity_resolution` stay false. The output contains no raw shared source_document; original inputs remain separate.

Input validation confirms the request can be evaluated, including valid requests with gaps. It is not a successful-result verdict. Inspect output status and unresolved_issues. Unknown/mismatched rights, denied or stale access, history conflicts, missing values, measured breaches and unobserved control targets remain review issues. Malformed types, identities, source links, shared artifacts or incompatible grain/units fail input validation.
