# Complete native input and output contract

Input is one JSON object. Required top-level fields: case_id (nonempty durable identifier); as_of (YYYY-MM-DD); context (object with nonempty capacity, represented_party, object_id, jurisdiction, line_of_business); sources (array of source_ref and version strings, with dated as_of required for this analytical method); unresolved_issues (explicit list of nonempty strings); data (fields below). Optional upstream_artifacts and context_mappings follow the bundled foundation contract. Source entries may also retain title, section, URL/path and extraction text; none grant authority.

All listed native keys are required. Structural objects/arrays cannot be null. Unknown scalar fields must be present as JSON null, which yields needs-data and no native arithmetic. Numbers may be JSON finite numbers or decimal strings; booleans are never numbers. Nonnegative >=0; positive >0; probability [0,1]; integer positive integral. Dates are real calendar dates. Currency is an uppercase three-letter code, with NONE permitted only for the count study. ref resolves exactly to a registered sources.source_ref. All monetary records carry object_id, currency and basis matching scope. No FX conversion occurs. Exact decimal arithmetic is used; PV exponentiation uses 34-digit precision and later totals use the Python decimal default context. No presentation rounding is imposed.

Profile fields establish source-bound method, object, product, jurisdiction, currency and effective dates; they are supplied assertions for specialist review, not institutional or legal certification. Scope.valuation_date equals case as_of. The method's required scalar enum values, sign/timing convention, supported empty arrays and numerical meanings are specified immediately below and in domain-rules.md.

| Field | Type | Presence and missingness |
| --- | --- | --- |
| `data.scope.object_id` | text or null | Required key; null remains an unresolved evidence gap. |
| `data.scope.currency` | currency or null | Required key; null remains an unresolved evidence gap. |
| `data.scope.basis` | text or null | Required key; null remains an unresolved evidence gap. |
| `data.scope.valuation_date` | date or null | Required key; null remains an unresolved evidence gap. |
| `data.profile.profile_id` | text or null | Required key; null remains an unresolved evidence gap. |
| `data.profile.version` | text or null | Required key; null remains an unresolved evidence gap. |
| `data.profile.source_refs` | array | Explicit list; empty only where the domain method permits. |
| `data.profile.source_refs[]` | ref or null | Required key; null remains an unresolved evidence gap. |
| `data.profile.jurisdictions` | array | Explicit list; empty only where the domain method permits. |
| `data.profile.jurisdictions[]` | text or null | Required key; null remains an unresolved evidence gap. |
| `data.profile.lines_of_business` | array | Explicit list; empty only where the domain method permits. |
| `data.profile.lines_of_business[]` | text or null | Required key; null remains an unresolved evidence gap. |
| `data.profile.effective_from` | date or null | Required key; null remains an unresolved evidence gap. |
| `data.profile.effective_to` | date or null | Required key; null remains an unresolved evidence gap. |
| `data.profile.object_ids` | array | Explicit list; empty only where the domain method permits. |
| `data.profile.object_ids[]` | text or null | Required key; null remains an unresolved evidence gap. |
| `data.profile.currencies` | array | Explicit list; empty only where the domain method permits. |
| `data.profile.currencies[]` | currency or null | Required key; null remains an unresolved evidence gap. |
| `data.profile.method` | text or null | Required key; null remains an unresolved evidence gap. |
| `data.study_start` | date or null | Required key; null remains an unresolved evidence gap. |
| `data.study_end` | date or null | Required key; null remains an unresolved evidence gap. |
| `data.event_type` | `death`, `lapse` or null | Required key. First terminal study event; null remains unresolved. |
| `data.segments` | array | Explicit list; empty only where the domain method permits. |
| `data.segments[].segment_id` | text or null | Required key; null remains an unresolved evidence gap. |
| `data.segments[].expected_intensity` | nonnegative or null | Required key; null remains an unresolved evidence gap. |
| `data.segments[].effective_from` | date or null | Required key; null remains an unresolved evidence gap. |
| `data.segments[].effective_to` | date or null | Required key; null remains an unresolved evidence gap. |
| `data.segments[].source_ref` | ref or null | Required key; null remains an unresolved evidence gap. |
| `data.exposures` | array | Explicit list; empty only where the domain method permits. |
| `data.exposures[].record_id` | text or null | Required key; null remains an unresolved evidence gap. |
| `data.exposures[].life_id` | text or null | Required key; null remains an unresolved evidence gap. |
| `data.exposures[].segment_id` | text or null | Required key; null remains an unresolved evidence gap. |
| `data.exposures[].entry_date` | date or null | Required key; null remains an unresolved evidence gap. |
| `data.exposures[].exit_date` | date or null | Required key; null remains an unresolved evidence gap. |
| `data.exposures[].exit_reason` | `event`, `censored` or null | Required key. `event` means the terminal event named by data.event_type; do not put a cause such as death in this field. `censored` includes withdrawal, study-end censoring and a segment transfer without the terminal event. Null remains unresolved. |
| `data.exposures[].source_ref` | ref or null | Required key; null remains an unresolved evidence gap. |

## Native meaning and allowed values

Clip each individual interval to the study window, then divide actual elapsed days by 365. Delayed entry begins at the later entry/study-start date. An observed event requires an event exit in (study_start, study_end] and positive observed time. Other exits and clipping at study-end are right censoring. At an event date the pre-event risk set has entry < event date <= exit. No exposure after a terminal study event and no overlapping same-life intervals are allowed. Adjacent censored intervals permit segment changes; the exiting segment receives a boundary event. Sum exposure and observed events by supplied segment; expected events = central exposure years times supplied constant annual intensity. Report observed central rate and actual/expected only with positive denominators. This is a counting-process intensity comparison, not multiplication of annual death probability by central exposure. Counts are individual lives; no monetary weights, annual q conversion, mortality table graduation, confidence interval, credibility weighting, or inference of independent censoring is implemented. The actuary must assess selection, censoring, segmentation, reporting lag and representativeness separately.

The exact scope.basis and profile.method value is `constant_intensity_act365_count`. ROW object IDs identify the same scope object; record IDs are unique within their collection. Profile.source_refs must be nonempty and scoped dates cover case as_of. Profile.object_ids and currencies must contain the scope values. No external policy is fetched by the executable.

Output uses the bundled foundation: producer, case_id, as_of, context, status, findings (code/message/severity/source_refs), results, completeness, evaluability, unresolved_issues, retained source_document and artifact. Every result is draft: action_taken false, human_review_required true, approval not_requested, execution not_performed. Native unavailable results are null rather than zero. Lists preserve row identities and provenance. See method formulas for result units; ratios are decimals, not percentages, and PV amounts use the supplied currency.
