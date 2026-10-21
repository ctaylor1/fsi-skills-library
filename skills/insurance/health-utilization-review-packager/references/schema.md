# Native schema

The required envelope is `case_id` (durable nonblank text), `as_of` (YYYY-MM-DD),
`context` {capacity, represented_party, object_id, jurisdiction, line_of_business},
`sources` [{source_ref, version, as_of, locator}], `unresolved_issues` (explicit list
of open questions), and `data` (object). Source IDs are unique, source dates known
and no later than review as_of. Every evidence row has nonempty `source_refs`
resolving those source IDs and a nonblank `locator` identifying actual source text.
The source locator and a reviewer name do not authenticate evidence.

`data.owner`, `market`, `program`, `product` are nonblank actual scope values.
The profile belongs at **data.profile**. Required profile keys: `profile_id`,
`version`, `reviewed_by`, `source_refs`, `jurisdictions`, `lines_of_business`,
`effective_from`, `effective_to`, `method`, `markets`, `programs`, `products`,
`rule_basis`, `limitations`. Arrays explicitly contain the actual scope. Profile
dates are inclusive around as_of; every criterion/code/contract/clock separately
has inclusive dates around its event basis. A region alone cannot select a rule.

Inventories are explicit arrays of objects with unique nonblank ID keys. Absent or
null inventories are unknown, never confirmed empty. Unknown factual values may
be null and produce dependent gaps; malformed non-null dates/numbers/types fail
structural validation. All required evidence fields must be supplied to obtain an
evaluable result. Decimal inputs use exact decimal strings; integer JSON numbers
are allowed. Fractional JSON floats, booleans, NaN and infinity are rejected.
Null numbers remain unknown. Numeric values are nonnegative unless stated signed. Arithmetic supports up to 256
significant digits and exponent magnitude 1000; overflow or any rounding requirement
fails closed rather than silently truncating.
`source_refs` and explicit string arrays contain nonblank references/tokens.

Optional `upstream_artifacts` and `context_mappings` follow workflow-contract.md.
One reviewed source-bound mapping is required for changed capacity, represented
party, object, jurisdiction or line. Unresolved upstream/input issues withhold
dependent arithmetic. Output retains immutable source_document, findings, native
results and artifact. Native decimal outputs are strings; unavailable values are
null. No output may promote action, approval, human review or execution flags.

## Utilization data

`context.capacity` is `payer-utilization-review`; `line_of_business` is `health`;
`object_id` equals request.request_id. `data.profile.method` is exactly
`health-utilization-evidence-v1`. Only the named payer case is packaged.

| Field | Required shape / meaning |
| --- | --- |
| `request` | Object; may be null for an incomplete draft |
| `request.request_id`, `member_token`, `provider_id`, `service_id`, `requested_service` | Nonblank source identities and requested-service description |
| `request.service_type` | `non-drug` or `drug`; classification is supplied, never inferred |
| `request.service_on` | Planned/actual service date YYYY-MM-DD; future service is allowed |
| `request.received_at` | UTC ISO timestamp ending Z or +00:00; not after as_of UTC day |
| `request.urgency` | `standard` or `expedited`; unknown remains null and withholds clock |
| `request.source_refs`, `locator` | Source bindings |
| `inventory` | Object with source_refs, locator, statement, criteria_complete, observations_complete |
| `inventory.statement` | Explicit source assertion defining complete case snapshot and scope |
| `inventory.criteria_complete`, `observations_complete` | Boolean/null; only sourced true supports complete evidence states |
| `assessment_at` | UTC ISO timestamp ending Z or +00:00, no earlier than receipt and not after as_of UTC day |
| `criteria` | Array keyed by criterion_id, at least one record |
| `criteria[].criterion_id`, `service_id`, `statement` | Unique criterion ID, exact requested service, supplied criterion statement |
| `criteria[].market`, `program`, `product` | Exact match to actual data scope; another plan rule is not applicable |
| `criteria[].kind` | `benefit` or `clinical` |
| `criteria[].mode` | `professional-observation` or `numeric-threshold` |
| `criteria[].version`, `reviewed_by`, `effective_from`, `effective_to` | Nonblank labels and inclusive dates covering request.service_on |
| `criteria[].source_refs`, `locator` | Versioned criterion evidence bindings |
| `criteria[].threshold`, `unit`, `comparator` | Required only for numeric-threshold: signed decimal, nonblank exact unit, `ge` / `le` / `eq` |
| `observations` | Explicit array keyed by observation_id; empty is allowed and leaves criteria unknown |
| `observations[].observation_id`, `criterion_id`, `request_id`, `service_id` | Exact unique observation and parent/request/service identities |
| `observations[].observed_on`, `summary` | Known date no later than as_of; source-bound summary |
| `observations[].contrary` | Explicit boolean, preserved even when criterion cannot be evaluated |
| `observations[].source_refs`, `locator` | Observation evidence bindings |
| `observations[].professional_reviewer`, `professional_role`, `state` | Professional mode only: named supplied qualified reviewer/role and `met` / `unmet` / `unknown` / `conflicting` |
| `observations[].value`, `unit` | Numeric mode only: signed exact decimal/null, same declared unit as criterion |
| `clock` | Supplied administrative rule object, or null when unavailable |
| `clock.rule_id`, `rule_basis` | Exact rule identifier and source-derived applicability explanation |
| `clock.market`, `program`, `product`, `service_type`, `urgency` | Exact match to actual data/request scope |
| `clock.start_event`, `clock.clock_basis` | Exactly `request-received` and `elapsed-hours` |
| `clock.hours` | Positive exact decimal, at most 87600 hours, representable in integer microseconds |
| `clock.version`, `reviewed_by`, `effective_from`, `effective_to` | Known rule labels; inclusive dates cover receipt UTC date |
| `clock.source_refs`, `locator` | Supplied applicable clock evidence |

## Output and missingness

`results.criteria[]` contains criterion_id/kind/mode, evidence_state, observation
IDs and per-observation states/contrary/source_refs. Aggregate evidence_state is
`met`, `unmet`, `unknown`, or `conflicting`. It is not a clinical finding generated
by the model. `clinical_appropriateness`, medical_necessity and benefit_decision
always remain `not_determined`. Raw observations and request are retained.

Arithmetic comparisons require exact unit equality; no conversion or reference
range inference occurs. Opposed met/unmet, explicit conflicting, or sourced contrary
observations require review. Unknown/missing evidence withholds its dependent state;
other criteria remain useful when the request scope and inventory are valid. Any missing
request identity, service classification, urgency, receipt or other request scope
keeps combined per-criterion evidence_state unknown; the attributed individual
observations are still preserved. Independence applies to one criterion's missing
observations versus another complete criterion, not to an invalid request scope.
Missing clinical observations do not erase a valid,
independently evidenced administrative clock. Remaining seconds are exact signed
decimals, avoiding rounded recurring fractions of an hour. Missing/incompatible clock inputs
return null administrative_target_utc and remaining_seconds, never a default deadline.
Business-day calendars, pauses, extensions and non-receipt clocks are unsupported.
