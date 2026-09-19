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
| `data.terms.object_id` | text or null | Required key; null remains an unresolved evidence gap. |
| `data.terms.currency` | currency or null | Required key; null remains an unresolved evidence gap. |
| `data.terms.basis` | text or null | Required key; null remains an unresolved evidence gap. |
| `data.terms.source_ref` | ref or null | Required key; null remains an unresolved evidence gap. |
| `data.terms.cedent_id` | text or null | Required key; null remains an unresolved evidence gap. |
| `data.terms.period_start` | date or null | Required key; null remains an unresolved evidence gap. |
| `data.terms.period_end` | date or null | Required key; null remains an unresolved evidence gap. |
| `data.terms.trigger_basis` | text or null | Required key; null remains an unresolved evidence gap. |
| `data.terms.loss_measure` | text or null | Required key; null remains an unresolved evidence gap. |
| `data.terms.inuring_basis` | text or null | Required key; null remains an unresolved evidence gap. |
| `data.terms.attachment` | nonnegative or null | Required key; null remains an unresolved evidence gap. |
| `data.terms.occurrence_limit` | positive or null | Required key; null remains an unresolved evidence gap. |
| `data.terms.annual_aggregate_limit` | positive or null | Required key; null remains an unresolved evidence gap. |
| `data.terms.participation` | probability or null | Required key; null remains an unresolved evidence gap. |
| `data.terms.gross_layer_premium` | nonnegative or null | Required key; null remains an unresolved evidence gap. |
| `data.terms.brokerage_rate` | probability or null | Required key; null remains an unresolved evidence gap. |
| `data.terms.commission_rate` | probability or null | Required key; null remains an unresolved evidence gap. |
| `data.terms.fixed_expense_at_signed_share` | nonnegative or null | Required key; null remains an unresolved evidence gap. |
| `data.terms.reinstatements` | nonnegative or null | Required key; null remains an unresolved evidence gap. |
| `data.terms.covered_perils` | array | Explicit list; empty only where the domain method permits. |
| `data.terms.covered_perils[]` | text or null | Required key; null remains an unresolved evidence gap. |
| `data.terms.covered_territories` | array | Explicit list; empty only where the domain method permits. |
| `data.terms.covered_territories[]` | text or null | Required key; null remains an unresolved evidence gap. |
| `data.scenarios` | array | Explicit list; empty only where the domain method permits. |
| `data.scenarios[].scenario_id` | text or null | Required key; null remains an unresolved evidence gap. |
| `data.scenarios[].probability` | probability or null | Required key; null remains an unresolved evidence gap. |
| `data.scenarios[].source_ref` | ref or null | Required key; null remains an unresolved evidence gap. |
| `data.scenarios[].events` | array | Explicit list; empty only where the domain method permits. |
| `data.scenarios[].events[].object_id` | text or null | Required key; null remains an unresolved evidence gap. |
| `data.scenarios[].events[].currency` | currency or null | Required key; null remains an unresolved evidence gap. |
| `data.scenarios[].events[].basis` | text or null | Required key; null remains an unresolved evidence gap. |
| `data.scenarios[].events[].source_ref` | ref or null | Required key; null remains an unresolved evidence gap. |
| `data.scenarios[].events[].event_id` | text or null | Required key; null remains an unresolved evidence gap. |
| `data.scenarios[].events[].event_date` | date or null | Required key; null remains an unresolved evidence gap. |
| `data.scenarios[].events[].peril` | text or null | Required key; null remains an unresolved evidence gap. |
| `data.scenarios[].events[].territory` | text or null | Required key; null remains an unresolved evidence gap. |
| `data.scenarios[].events[].loss_measure` | text or null | Required key; null remains an unresolved evidence gap. |
| `data.scenarios[].events[].inuring_basis` | text or null | Required key; null remains an unresolved evidence gap. |
| `data.scenarios[].events[].loss` | nonnegative or null | Required key; null remains an unresolved evidence gap. |
| `data.wording_exceptions` | array | Explicit list; empty only where the domain method permits. |
| `data.wording_exceptions[].clause` | text or null | Required key; null remains an unresolved evidence gap. |
| `data.wording_exceptions[].issue` | text or null | Required key; null remains an unresolved evidence gap. |
| `data.wording_exceptions[].source_ref` | ref or null | Required key; null remains an unresolved evidence gap. |

## Native meaning and allowed values

Required exact values: `context.capacity=assuming_reinsurer`; `data.terms.trigger_basis=losses_occurring`; `data.terms.loss_measure=ultimate_loss_including_lae`; `data.terms.inuring_basis=net_of_scheduled_inuring`; `data.terms.reinstatements=0`. Every event must repeat those exact loss_measure and inuring_basis values. These underscore spellings are part of the native interface; natural-language equivalents are not silently translated.

Only assumed losses-occurring occurrence XOL with zero reinstatements is supported. Treaty period is [start,end), and perils and territories are explicit covered sets. Supplied scenario event loss is ultimate loss including LAE, already net of scheduled inuring reinsurance. Events on other bases block arithmetic; no gross-to-net inference is made. For covered events, occurrence layer loss = min(max(loss-attachment,0), occurrence limit). Apply the remaining annual aggregate at 100% of the layer in chronological date/event-ID order, then multiply by signed participation. All limits and gross layer premium are at 100% layer; fixed expense is already at the signed share. Signed premium = layer premium*participation; brokerage and commission rates apply to signed premium. Net underwriting cashflow = signed premium - signed losses - variable and fixed expenses. Weight by supplied exhaustive scenario probabilities summing exactly to one; do not renormalize missing tails. Report negative-cashflow probability and expected loss ratio, not legal risk transfer, return on capital or an acceptable price. Wording exceptions remain open even when arithmetic ties. Hours clauses, event aggregation, coverage interpretation, reinstatements, sliding-scale commissions, profit commissions, aggregate deductibles, funds withheld, discounting and retrospective premiums are not implemented. Event losses must already reflect any such external preprocessing supported by the allowed simple terms.

The exact scope.basis and profile.method value is `assumed_occurrence_xol_no_reinstatement`. ROW object IDs identify the same scope object; record IDs are unique within their collection. Profile.source_refs must be nonempty and scoped dates cover case as_of. Profile.object_ids and currencies must contain the scope values. No external policy is fetched by the executable.

Output uses the bundled foundation: producer, case_id, as_of, context, status, findings (code/message/severity/source_refs), results, completeness, evaluability, unresolved_issues, retained source_document and artifact. Every result is draft: action_taken false, human_review_required true, approval not_requested, execution not_performed. Native unavailable results are null rather than zero. Lists preserve row identities and provenance. See method formulas for result units; ratios are decimals, not percentages, and PV amounts use the supplied currency.
