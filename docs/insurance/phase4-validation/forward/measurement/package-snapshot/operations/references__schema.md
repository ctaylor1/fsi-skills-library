# Native schema

Required top-level keys: case_id (durable nonempty text), as_of (YYYY-MM-DD), context {capacity,represented_party,object_id,jurisdiction,line_of_business}, sources [{source_ref,version,as_of, optional locator}], unresolved_issues (explicit list of open questions), data (object). Source IDs are unique; every source date is known and no later than as_of. Unknown context is explicit unknown, which keeps outputs partial.

All data fields below are required unless explicitly marked optional in the method. Inventories are explicit arrays of objects with unique nonblank IDs; a missing/null inventory is unknown, never confirmed empty. Null numeric values preserve missingness. Numeric inputs allow finite decimal strings/numbers, never booleans/NaN/infinity; nonnegative unless the method permits signed values. Probabilities/fractions are in [0,1], counts/attempts/waves are integral. All source_refs arrays must identify supplied versioned records.

The review profile is nested at **data.profile** (not top level). Required profile keys: profile_id, version, reviewed_by, source_refs, jurisdictions and lines_of_business (explicit arrays containing context), effective_from/effective_to inclusive around as_of, and method exactly `complete-episode-window-performance-v1`. A supplied profile is not authenticated approval.

## Data fields

| Field | Shape |
| --- | --- |
| `data.population` | text or null |
| `data.definition_version` | text or null |
| `data.currency` | text or null |
| `data.owner` | text or null |
| `data.inventory_complete` | boolean |
| `data.window_start` | ISO timestamp or null |
| `data.window_end` | ISO timestamp or null |
| `data.sla_hours` | finite number or null |
| `data.sla_clock` | text or null |
| `data.reported_opening` | finite number or null |
| `data.reported_closing` | finite number or null |
| `data.available_labor_hours` | finite number or null |
| `data.worked_labor_hours` | finite number or null |
| `data.episodes` | array of objects |
| `data.episodes[].episode_id` | text or null |
| `data.episodes[].population` | text or null |
| `data.episodes[].definition_version` | text or null |
| `data.episodes[].currency` | text or null |
| `data.episodes[].created_at` | ISO timestamp or null |
| `data.episodes[].exited_at` | ISO timestamp or null |
| `data.episodes[].exit_kind` | text or null |
| `data.episodes[].cost` | finite number or null |
| `data.episodes[].human_minutes` | finite number or null |
| `data.episodes[].source_refs` | explicit array of unique strings |

## Exact enums and semantic requirements

The supported method is `complete-episode-window-performance-v1`, with sla_clock=elapsed-calendar-hours. All timestamps require explicit timezones and normalize to UTC. A complete snapshot includes episodes open at start and every arrival through the window; episode IDs are unique, so reopening requires a distinct linked episode upstream. Window is [start,end). Opening = created before start and not exited before start; arrivals fall in the window; completed/cancelled exits fall in the window; closing = created before end and not exited before end. Opening + arrivals - completed - cancelled = closing; independently supplied opening/closing counts are also compared. Completed-cohort duration is exit minus creation, including pre-window age, measured in calendar hours. Cancelled and still-open episodes are excluded from completed means, cost and SLA fraction; backlog ages are shown separately. p95 is nearest rank ceil(.95*n), not interpolation. Cost and labor per completed episode use only those completed episodes, not full-window overhead; do not call it fully allocated cost. Worked/available labor hours must describe the same window; zero capacity yields null utilization. Empty complete snapshots produce zero counts and unknown denominators. Inventory, method or evidence gaps withhold window aggregates. No Little's Law projection, business-day deadline or causal staffing recommendation is made.

Optional upstream_artifacts and context_mappings follow workflow-contract.md. All outputs retain source_document, context, findings, native results, unresolved_issues and artifact. Native results use Decimal strings; ratios are fractions except explicitly labeled minutes/hours or counts. Unknown measures are null. No action, approval or execution flags can be promoted.


## Conditional fields and exact vocabulary

Open episodes use exited_at=null and exit_kind=null. Only episodes completed inside the observation window require cost and human_minutes; these fields may be null or absent for open, cancelled or out-of-window episodes. A supplied non-null amount must still be finite and nonnegative.

Unclassified top-level or upstream unresolved issues conservatively withhold dependent measurements and recommendations. Keep all unresolved issues; do not remove them to obtain a complete result. Content hashes establish identity, not source authenticity.

A known opening/closing control difference yields needs-review and snapshot_reconciled=false. Counts and completed-cohort measures then describe only the supplied extract, not an accepted complete population. Show the control differences and qualify those values in the deliverable. Unknown completeness/scope or required completed-cohort inputs withhold dependent aggregates. Non-completed episodes do not need cost/labor values.
