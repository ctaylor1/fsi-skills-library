# Input field inventory

Every new-mode request has `request_id`, `object_id`, `as_of`, `knowledge_cutoff`, `currency`, `audience: internal-review`, and nonempty `sources`. Dates are strict YYYY-MM-DD. Currency uses one stated ISO-style code; there is no FX conversion of mixed-currency records. Decimal inputs reject booleans, missing values, infinities and excessive magnitudes. Reported amounts use six decimal places; analytic ratios use explicit twelve-place rounding.

Every business row is exactly `{source_ref, claim_id, data}`. Its source entry contains `source_ref`, `version`, `as_of`, `known_at`, `object_id`, `currency`, `permitted_audiences`, and `claims`, where `claims[claim_id]` must exactly equal the row data. Known-at cannot exceed the request cutoff; an observation dated after as-of is withheld. Identity/currency and audience must match before any row values, identifiers or provenance are copied. Restricted evidence generates a generic omission; source_refs and ledgers include only used evidence.

A policy, approved answer, approval record or message additionally requires source `approval_status: approved`, `effective_from`, and `expires`. Policy/content data also carry their own effective_from/expires when specified below. Both intervals must include as-of. These are supplied records, not authenticated signatures. A known source ID or a matching hash alone never establishes source truth.

`calculate_or_transform.py INPUT.json` emits an internal draft. `validate_input.py INPUT.json` checks executable inputs. `validate_output.py OUTPUT.json --input INPUT.json` reconstructs the complete result against the detached original and rejects changed or extra fields. No new mode embeds source_input. Unknown top-level fields/modes are rejected. Valid incomplete evidence yields a needs-review draft, not a fabricated complete packet.


## institutional

Fixture: `evals/files/institutional.json`. Required domain groups and claim data fields:

- `manager`: source-bound object; data fields `id`, `strategy_aum`, `capacity_aum`, `proposed_commitment`.
- `policy`: source-bound object; data fields `id`, `effective_from`, `expires`, `scoring_method`, `criteria`.
- `evidence`: source-bound rows; data fields `id`, `criterion_id`, `origin`, `value`. Each list uses unique data.id.
- `fee_terms`: source-bound object; data fields `id`, `capital`, `management_bps`, `other_bps`, `method`.
- `performance`: source-bound object; data fields `id`, `basis`, `reconciled`, `period_end`, `manager_return`, `benchmark_return`, `benchmark_id`.

Amounts use the request currency without currency conversion. Returns/weights are fractions (0.05 means5%); fee rates are annual basis points. IDs, owners, dates, values, thresholds and approved text are supplied facts. Source-exact data fields are interpreted only as described by the domain method; unused narrative is never copied into results.

## Nested institutional policy and evidence fields

Use explicit `mode: institutional`. Every policy `criteria` item requires `id`, `dimension`, `operator`, `threshold`, `required`, `independent_required`, and `weight`. IDs must be unique. Dimensions are exactly `investment`, `operations`, `team`, `capacity`, `fees`, and `performance`; complete policy coverage includes all six. The two flags are explicit booleans and weight is a nonnegative decimal. Operators are `minimum` (numeric >=), `maximum` (numeric <=), `equals` (same value and type), and `documented` (true met / false not met; supply `threshold: true`). Missing or duplicate evidence for a criterion stays unknown.

Evidence links by `criterion_id`. `origin: independent` is required when the criterion sets `independent_required: true`; `manager-reported` cannot satisfy that requirement. These origin labels remain supplied assertions. Only `scoring_method: weighted-met-fraction` requests a score; `none` or null requests no scoring. Score = sum of weights for met criteria / all criterion weights, and is withheld for unknown evidence, unmet required criteria, incomplete six-dimension coverage, or nonpositive total weight. No ranking is produced.

Fee method is `flat-management-and-expense-only`; unsupported incentive/tier/waterfall terms are unresolved. Performance requires `basis: net`, `reconciled: true`, a real period_end no later than as-of, benchmark ID, and fractional manager and benchmark returns no lower than -1. Fee terms and performance are supplied evidence, not certified calculations or external verification.

Actual completed observation dates (AUM/report/performance period_end, service opened_at/last_delivered, RFP recorded_at where present) must be on or before request as_of, knowledge_cutoff, and that row’s supporting source known_at. A later actual observation is rejected or withheld. Prospective scenarios, due dates, review-by dates, and effective/expiry intervals retain their documented planning meaning.
