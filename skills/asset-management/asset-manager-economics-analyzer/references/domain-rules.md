# Method and bounded behavior

AUM opening + subscriptions - redemptions + performance change + FX change + other change = closing. Annualized revenue uses average billable AUM × annual fee bps /10,000 plus other revenue. Cost uses variable cost bps, direct fixed cost and allocated overhead. Product/revenue mix uses complete reconciled books. Stress applies redemptions, market return, then new sales; adjusts fee bps and incremental costs. Unreconciled product books cannot support aggregate closing AUM or scenarios.

Every new-mode request has `request_id`, `object_id`, `as_of`, `knowledge_cutoff`, `currency`, `audience: internal-review`, and nonempty `sources`. Dates are strict YYYY-MM-DD. Currency uses one stated ISO-style code; there is no FX conversion of mixed-currency records. Decimal inputs reject booleans, missing values, infinities and excessive magnitudes. Reported amounts use six decimal places; analytic ratios use explicit twelve-place rounding.

Every business row is exactly `{source_ref, claim_id, data}`. Its source entry contains `source_ref`, `version`, `as_of`, `known_at`, `object_id`, `currency`, `permitted_audiences`, and `claims`, where `claims[claim_id]` must exactly equal the row data. Known-at cannot exceed the request cutoff; an observation dated after as-of is withheld. Identity/currency and audience must match before any row values, identifiers or provenance are copied. Restricted evidence generates a generic omission; source_refs and ledgers include only used evidence.

A policy, approved answer, approval record or message additionally requires source `approval_status: approved`, `effective_from`, and `expires`. Policy/content data also carry their own effective_from/expires when specified below. Both intervals must include as-of. These are supplied records, not authenticated signatures. A known source ID or a matching hash alone never establishes source truth.

`calculate_or_transform.py INPUT.json` emits an internal draft. `validate_input.py INPUT.json` checks executable inputs. `validate_output.py OUTPUT.json --input INPUT.json` reconstructs the complete result against the detached original and rejects changed or extra fields. No new mode embeds source_input. Unknown top-level fields/modes are rejected. Valid incomplete evidence yields a needs-review draft, not a fabricated complete packet.

Missing information stays unresolved. Policy assertions are never regulatory opinions, and documented approvals cannot authorize this code to act.
