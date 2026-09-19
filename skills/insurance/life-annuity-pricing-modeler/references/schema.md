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
| `data.initial_policies` | positive or null | Required key; null remains an unresolved evidence gap. |
| `data.projection_end_year` | integer or null | Required key; null remains an unresolved evidence gap. |
| `data.years` | array | Explicit list; empty only where the domain method permits. |
| `data.years[].object_id` | text or null | Required key; null remains an unresolved evidence gap. |
| `data.years[].currency` | currency or null | Required key; null remains an unresolved evidence gap. |
| `data.years[].basis` | text or null | Required key; null remains an unresolved evidence gap. |
| `data.years[].source_ref` | ref or null | Required key; null remains an unresolved evidence gap. |
| `data.years[].year` | integer or null | Required key; null remains an unresolved evidence gap. |
| `data.years[].mortality_probability` | probability or null | Required key; null remains an unresolved evidence gap. |
| `data.years[].lapse_probability` | probability or null | Required key; null remains an unresolved evidence gap. |
| `data.years[].premium` | nonnegative or null | Required key; null remains an unresolved evidence gap. |
| `data.years[].expense_boy` | nonnegative or null | Required key; null remains an unresolved evidence gap. |
| `data.years[].death_benefit` | nonnegative or null | Required key; null remains an unresolved evidence gap. |
| `data.years[].surrender_benefit` | nonnegative or null | Required key; null remains an unresolved evidence gap. |
| `data.years[].survival_benefit` | nonnegative or null | Required key; null remains an unresolved evidence gap. |
| `data.years[].discount_rate` | number or null | Required key; null remains an unresolved evidence gap. |
| `data.terminal_benefit_per_survivor` | nonnegative or null | Required key; null remains an unresolved evidence gap. |
| `data.terminal_source_ref` | ref or null | Required key; null remains an unresolved evidence gap. |

## Native meaning and allowed values

At the start of year t, N_t policies pay the supplied premium and expense. Deaths = N_t*q_t; lapses = N_t*l_t; closing survivors = N_t*(1-q_t-l_t). Both decrements are unconditional mutually exclusive probabilities of the opening population, so their sum cannot exceed one. EOY benefit = deaths*death benefit + lapses*surrender benefit + closing survivors*survival benefit. An explicit additional terminal benefit is paid to final survivors only; avoid duplicating it in the final survival benefit. Premiums and expenses discount at BOY; benefits at EOY. Supplied annual forward rates accumulate through consecutive years. Sum PV premiums less expenses and benefits for discounted net cashflow and divide by PV premiums for a cashflow margin. These are cashflow metrics, not statutory earnings, embedded value, distributable profit, IRR or price adequacy. Product/rider guarantees, optionality, dynamic lapse behavior, capital, taxes, reserves, investments and cashflows after the explicit terminal payment are outside this small model. Use separate coherent source-backed inputs for sensitivities; no probability conversion or target premium solve is inferred.

The exact scope.basis and profile.method value is `annual_mutually_exclusive_decrement_cashflow`. ROW object IDs identify the same scope object; record IDs are unique within their collection. Profile.source_refs must be nonempty and scoped dates cover case as_of. Profile.object_ids and currencies must contain the scope values. No external policy is fetched by the executable.

Output uses the bundled foundation: producer, case_id, as_of, context, status, findings (code/message/severity/source_refs), results, completeness, evaluability, unresolved_issues, retained source_document and artifact. Every result is draft: action_taken false, human_review_required true, approval not_requested, execution not_performed. Native unavailable results are null rather than zero. Lists preserve row identities and provenance. See method formulas for result units; ratios are decimals, not percentages, and PV amounts use the supplied currency.
