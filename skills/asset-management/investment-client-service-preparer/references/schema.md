# Input field inventory

Every new-mode request has `request_id`, `object_id`, `as_of`, `knowledge_cutoff`, `currency`, `audience: internal-review`, and nonempty `sources`. Dates are strict YYYY-MM-DD. Currency uses one stated ISO-style code; there is no FX conversion of mixed-currency records. Decimal inputs reject booleans, missing values, infinities and excessive magnitudes. Reported amounts use six decimal places; analytic ratios use explicit twelve-place rounding.

Every business row is exactly `{source_ref, claim_id, data}`. Its source entry contains `source_ref`, `version`, `as_of`, `known_at`, `object_id`, `currency`, `permitted_audiences`, and `claims`, where `claims[claim_id]` must exactly equal the row data. Known-at cannot exceed the request cutoff; an observation dated after as-of is withheld. Identity/currency and audience must match before any row values, identifiers or provenance are copied. Restricted evidence generates a generic omission; source_refs and ledgers include only used evidence.

A policy, approved answer, approval record or message additionally requires source `approval_status: approved`, `effective_from`, and `expires`. Policy/content data also carry their own effective_from/expires when specified below. Both intervals must include as-of. These are supplied records, not authenticated signatures. A known source ID or a matching hash alone never establishes source truth.

`calculate_or_transform.py INPUT.json` emits an internal draft. `validate_input.py INPUT.json` checks executable inputs. `validate_output.py OUTPUT.json --input INPUT.json` reconstructs the complete result against the detached original and rejects changed or extra fields. No new mode embeds source_input. Unknown top-level fields/modes are rejected. Valid incomplete evidence yields a needs-review draft, not a fabricated complete packet.


## service

Fixture: `evals/files/service.json`. Required domain groups and claim data fields:

- `service_policy`: source-bound object; data fields `id`, `effective_from`, `expires`, `sla_days`.
- `issues`: source-bound rows; data fields `id`, `status`, `severity`, `owner`, `opened_at`, `due_at`, `resolution_evidence_recorded`. Each list uses unique data.id.
- `reports`: source-bound rows; data fields `id`, `owner`, `last_delivered`, `cadence_days`. Each list uses unique data.id.
- `messages`: source-bound rows; data fields `id`, `effective_from`, `expires`, `text`. Each list uses unique data.id.

Amounts use the request currency without currency conversion. Returns/weights are fractions (0.05 means5%); fee rates are annual basis points. IDs, owners, dates, values, thresholds and approved text are supplied facts. Source-exact data fields are interpreted only as described by the domain method; unused narrative is never copied into results.

This package has one native method. Omit `mode`; any supplied mode selector is rejected.

Actual completed observation dates (AUM/report/performance period_end, service opened_at/last_delivered, RFP recorded_at where present) must be on or before request as_of, knowledge_cutoff, and that row’s supporting source known_at. A later actual observation is rejected or withheld. Prospective scenarios, due dates, review-by dates, and effective/expiry intervals retain their documented planning meaning.
