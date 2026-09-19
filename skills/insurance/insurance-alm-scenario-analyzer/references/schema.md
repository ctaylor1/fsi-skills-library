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
| `data.horizon_end` | date or null | Required key; null remains an unresolved evidence gap. |
| `data.opening_cash` | nonnegative or null | Required key; null remains an unresolved evidence gap. |
| `data.cash_source_ref` | ref or null | Required key; null remains an unresolved evidence gap. |
| `data.cashflows` | array | Explicit list; empty only where the domain method permits. |
| `data.cashflows[].object_id` | text or null | Required key; null remains an unresolved evidence gap. |
| `data.cashflows[].currency` | currency or null | Required key; null remains an unresolved evidence gap. |
| `data.cashflows[].basis` | text or null | Required key; null remains an unresolved evidence gap. |
| `data.cashflows[].source_ref` | ref or null | Required key; null remains an unresolved evidence gap. |
| `data.cashflows[].cashflow_id` | text or null | Required key; null remains an unresolved evidence gap. |
| `data.cashflows[].side` | text or null | Required key; null remains an unresolved evidence gap. |
| `data.cashflows[].payment_date` | date or null | Required key; null remains an unresolved evidence gap. |
| `data.cashflows[].amount` | nonnegative or null | Required key; null remains an unresolved evidence gap. |
| `data.curve` | array | Explicit list; empty only where the domain method permits. |
| `data.curve[].payment_date` | date or null | Required key; null remains an unresolved evidence gap. |
| `data.curve[].spot_rate` | number or null | Required key; null remains an unresolved evidence gap. |
| `data.curve[].source_ref` | ref or null | Required key; null remains an unresolved evidence gap. |
| `data.scenarios` | array | Explicit list; empty only where the domain method permits. |
| `data.scenarios[].scenario_id` | text or null | Required key; null remains an unresolved evidence gap. |
| `data.scenarios[].parallel_rate_shift` | number or null | Required key; null remains an unresolved evidence gap. |
| `data.scenarios[].asset_receipt_multiplier` | nonnegative or null | Required key; null remains an unresolved evidence gap. |
| `data.scenarios[].liability_payment_multiplier` | nonnegative or null | Required key; null remains an unresolved evidence gap. |
| `data.scenarios[].source_ref` | ref or null | Required key; null remains an unresolved evidence gap. |

## Native meaning and allowed values

The input represents nonnegative supporting asset receipts and nonnegative liability payments. Opening cash is separate; do not include it again as an asset cashflow. Supply one annual-effective spot rate for each exact future payment date; no curve interpolation or extrapolation occurs. Each scenario applies its parallel rate shift to the same date curve for both sides, with explicit side-specific cashflow multipliers. Compute PV at actual days/365; surplus = opening cash + asset cashflow PV - liability cashflow PV. Report change from the required unshocked base. PV-weighted times are weighted maturities, not modified/effective duration or a hedge ratio. Independently net receipts/payments by date and cumulate from opening cash with no interest, reinvestment, borrowing or asset sales. Funding gap is the magnitude of the most negative cumulative cash. Same-day flows net together; intraday liquidity is unmodeled. Static fixed cashflows do not reflect rate-sensitive surrenders, prepayments, defaults, hedges, or management actions. This is deterministic sensitivity analysis, not a stochastic asset-adequacy test or solvency opinion.

The exact scope.basis and profile.method value is `static_cashflow_alm_act365`. ROW object IDs identify the same scope object; record IDs are unique within their collection. Profile.source_refs must be nonempty and scoped dates cover case as_of. Profile.object_ids and currencies must contain the scope values. No external policy is fetched by the executable.

Output uses the bundled foundation: producer, case_id, as_of, context, status, findings (code/message/severity/source_refs), results, completeness, evaluability, unresolved_issues, retained source_document and artifact. Every result is draft: action_taken false, human_review_required true, approval not_requested, execution not_performed. Native unavailable results are null rather than zero. Lists preserve row identities and provenance. See method formulas for result units; ratios are decimals, not percentages, and PV amounts use the supplied currency.
