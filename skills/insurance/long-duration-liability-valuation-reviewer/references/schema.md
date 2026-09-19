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
| `data.profile.accounting_basis` | text or null | Required key; null remains an unresolved evidence gap. |
| `data.profile.rounding_tolerance` | nonnegative or null | Required key; null remains an unresolved evidence gap. |
| `data.accounting_basis` | text or null | Required key; null remains an unresolved evidence gap. |
| `data.projection_horizon_end` | date or null | Required key; null remains an unresolved evidence gap. |
| `data.cashflows` | array | Explicit list; empty only where the domain method permits. |
| `data.cashflows[].object_id` | text or null | Required key; null remains an unresolved evidence gap. |
| `data.cashflows[].currency` | currency or null | Required key; null remains an unresolved evidence gap. |
| `data.cashflows[].basis` | text or null | Required key; null remains an unresolved evidence gap. |
| `data.cashflows[].source_ref` | ref or null | Required key; null remains an unresolved evidence gap. |
| `data.cashflows[].cashflow_id` | text or null | Required key; null remains an unresolved evidence gap. |
| `data.cashflows[].payment_date` | date or null | Required key; null remains an unresolved evidence gap. |
| `data.cashflows[].kind` | text or null | Required key; null remains an unresolved evidence gap. |
| `data.cashflows[].amount` | nonnegative or null | Required key; null remains an unresolved evidence gap. |
| `data.cashflows[].spot_rate` | number or null | Required key; null remains an unresolved evidence gap. |
| `data.balances.object_id` | text or null | Required key; null remains an unresolved evidence gap. |
| `data.balances.currency` | currency or null | Required key; null remains an unresolved evidence gap. |
| `data.balances.basis` | text or null | Required key; null remains an unresolved evidence gap. |
| `data.balances.source_ref` | ref or null | Required key; null remains an unresolved evidence gap. |
| `data.balances.opening_date` | date or null | Required key; null remains an unresolved evidence gap. |
| `data.balances.closing_date` | date or null | Required key; null remains an unresolved evidence gap. |
| `data.balances.opening_liability` | number or null | Required key; null remains an unresolved evidence gap. |
| `data.balances.closing_liability` | number or null | Required key; null remains an unresolved evidence gap. |
| `data.balances.reported_cashflow_pv` | number or null | Required key; null remains an unresolved evidence gap. |
| `data.movements` | array | Explicit list; empty only where the domain method permits. |
| `data.movements[].object_id` | text or null | Required key; null remains an unresolved evidence gap. |
| `data.movements[].currency` | currency or null | Required key; null remains an unresolved evidence gap. |
| `data.movements[].basis` | text or null | Required key; null remains an unresolved evidence gap. |
| `data.movements[].source_ref` | ref or null | Required key; null remains an unresolved evidence gap. |
| `data.movements[].movement_id` | text or null | Required key; null remains an unresolved evidence gap. |
| `data.movements[].movement_date` | date or null | Date after opening and through closing balance date. |
| `data.movements[].amount` | number or null | Required key; null remains an unresolved evidence gap. |
| `data.movements[].reason` | text or null | Required key; null remains an unresolved evidence gap. |
| `data.pv_to_book_adjustments` | array | Explicit list; empty only where the domain method permits. |
| `data.pv_to_book_adjustments[].object_id` | text or null | Required key; null remains an unresolved evidence gap. |
| `data.pv_to_book_adjustments[].currency` | currency or null | Required key; null remains an unresolved evidence gap. |
| `data.pv_to_book_adjustments[].basis` | text or null | Required key; null remains an unresolved evidence gap. |
| `data.pv_to_book_adjustments[].source_ref` | ref or null | Required key; null remains an unresolved evidence gap. |
| `data.pv_to_book_adjustments[].adjustment_id` | text or null | Required key; null remains an unresolved evidence gap. |
| `data.pv_to_book_adjustments[].valuation_date` | date or null | Must equal case as_of. |
| `data.pv_to_book_adjustments[].amount` | number or null | Required key; null remains an unresolved evidence gap. |
| `data.pv_to_book_adjustments[].reason` | text or null | Required key; null remains an unresolved evidence gap. |

## Native meaning and allowed values

Cashflows are supplied expected amounts already reflecting decrements and probabilities. Do not survival-weight them again. Benefits and expenses are positive liability outflows; premiums are negative. Recompute PV using each row's supplied annual-effective spot rate and actual elapsed days/365. Compare total to reported cashflow PV; add explicit signed PV-to-book adjustments and compare to book liability; independently reconcile opening liability plus signed movements dated after opening through closing to closing liability. PV-to-book adjustments must be valued at as_of. Compare absolute residuals to the rounding tolerance explicitly supplied in the sourced profile. No materiality threshold is invented. Both balance dates, same object/currency/calculation basis, accounting basis, projection dates and provenance must match. This does not choose a reserve method, net premium ratio, risk adjustment, cohort, discount curve, floor, statutory minimum, VM-20/VM-21 reserve, GAAP LDTI liability or IFRS 17 measurement. A fully tied bridge proves arithmetic only; source-model adequacy and the completeness of the projection horizon remain professional review matters.

The exact scope.basis and profile.method value is `supplied_liability_cashflow_pv_act365`. ROW object IDs identify the same scope object; record IDs are unique within their collection. Profile.source_refs must be nonempty and scoped dates cover case as_of. Profile.object_ids and currencies must contain the scope values. No external policy is fetched by the executable.

Output uses the bundled foundation: producer, case_id, as_of, context, status, findings (code/message/severity/source_refs), results, completeness, evaluability, unresolved_issues, retained source_document and artifact. Every result is draft: action_taken false, human_review_required true, approval not_requested, execution not_performed. Native unavailable results are null rather than zero. Lists preserve row identities and provenance. See method formulas for result units; ratios are decimals, not percentages, and PV amounts use the supplied currency.
