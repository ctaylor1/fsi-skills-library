# Native schema

Required top-level keys: case_id (durable nonempty text), as_of (YYYY-MM-DD), context {capacity,represented_party,object_id,jurisdiction,line_of_business}, sources [{source_ref,version,as_of, optional locator}], unresolved_issues (explicit list of open questions), data (object). Source IDs are unique; every source date is known and no later than as_of. Unknown context is explicit unknown, which keeps outputs partial.

All data fields below are required unless explicitly marked optional in the method. Inventories are explicit arrays of objects with unique nonblank IDs; a missing/null inventory is unknown, never confirmed empty. Null numeric values preserve missingness. Numeric inputs allow finite decimal strings/numbers, never booleans/NaN/infinity; nonnegative unless the method permits signed values. Probabilities/fractions are in [0,1], counts/attempts/waves are integral. All source_refs arrays must identify supplied versioned records.

The review profile is nested at **data.profile** (not top level). Required profile keys: profile_id, version, reviewed_by, source_refs, jurisdictions and lines_of_business (explicit arrays containing context), effective_from/effective_to inclusive around as_of, and method exactly `insurance-temporal-data-contract-v1`. A supplied profile is not authenticated approval.

## Data fields

| Field | Shape |
| --- | --- |
| `data.valid_on` | calendar date or null |
| `data.known_on` | calendar date or null |
| `data.sample_inventory_complete` | boolean |
| `data.purpose` | text or null |
| `data.owner` | text or null |
| `data.grain` | text or null |
| `data.retention_rule` | text or null |
| `data.entities` | array of objects |
| `data.entities[].entity_id` | text or null |
| `data.entities[].entity_type` | text or null |
| `data.entities[].identity_namespace` | text or null |
| `data.entities[].source_key` | text or null |
| `data.entities[].source_refs` | explicit array of unique strings |
| `data.fields` | array of objects |
| `data.fields[].field_id` | text or null |
| `data.fields[].entity_type` | text or null |
| `data.fields[].definition` | text or null |
| `data.fields[].unit` | text or null |
| `data.fields[].source_system` | text or null |
| `data.fields[].source_field` | text or null |
| `data.fields[].transformation` | text or null |
| `data.fields[].owner` | text or null |
| `data.fields[].classification` | text or null |
| `data.fields[].access_rule` | text or null |
| `data.fields[].quality_rule` | text or null |
| `data.fields[].version` | text or null |
| `data.fields[].purpose_reviewed` | boolean |
| `data.fields[].required` | boolean |
| `data.fields[].source_refs` | explicit array of unique strings |
| `data.relations` | array of objects |
| `data.relations[].relation_id` | text or null |
| `data.relations[].from_type` | text or null |
| `data.relations[].to_type` | text or null |
| `data.relations[].definition` | text or null |
| `data.relations[].cardinality` | text or null |
| `data.relations[].source_refs` | explicit array of unique strings |
| `data.links` | array of objects |
| `data.links[].link_id` | text or null |
| `data.links[].relation_id` | text or null |
| `data.links[].left_entity_id` | text or null |
| `data.links[].right_entity_id` | text or null |
| `data.links[].source_refs` | explicit array of unique strings |
| `data.records` | array of objects |
| `data.records[].record_id` | text or null |
| `data.records[].entity_id` | text or null |
| `data.records[].field_id` | text or null |
| `data.records[].valid_from` | calendar date or null |
| `data.records[].valid_to` | calendar date or null |
| `data.records[].recorded_on` | calendar date or null |
| `data.records[].value` | JSON value or null |
| `data.records[].source_refs` | explicit array of unique strings |

## Exact enums and semantic requirements

The supported method is `insurance-temporal-data-contract-v1`. The declared grain, field definition/unit, source column, transformation, owner, classification, access and quality rules constitute a draft semantic contract. Sample assertions use [valid_from, valid_to); null valid_to means open-ended. Resolve only assertions effective on valid_on and recorded no later than known_on, with both query dates no later than review as_of. Multiple active assertions are a conflict even if their values match; never silently select the latest source. Required fields need a single known value. Exact supplied entity links must satisfy entity types and one-to-one or many-to-one cardinality. IDs remain namespaced; there is no fuzzy matching, implicit join, deployed pipeline or ACORD conformance test. Any contract/sample gap withholds resolved values, retaining source record identities and conflict evidence. Optional absent fields remain null.

Optional upstream_artifacts and context_mappings follow workflow-contract.md. All outputs retain source_document, context, findings, native results, unresolved_issues and artifact. Native results use Decimal strings; ratios are fractions except explicitly labeled minutes/hours or counts. Unknown measures are null. No action, approval or execution flags can be promoted.


## Conditional fields and exact vocabulary

records[].valid_to is a calendar date or null for an open-ended interval. fields[].required is boolean. A field that is optional and has no active assertion resolves to null without inventing a value.

Unclassified top-level or upstream unresolved issues conservatively withhold dependent measurements and recommendations. Keep all unresolved issues; do not remove them to obtain a complete result. Content hashes establish identity, not source authenticity.
