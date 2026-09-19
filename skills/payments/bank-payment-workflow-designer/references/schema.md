# Input and artifact contract

Use [input-schema.json](input-schema.json) for the envelope, the native validator for exact structure, and `evals/files/normal.json` as a synthetic worked example. All money is a nonnegative decimal string with explicit currency; missing is not zero. Source IDs must resolve in the envelope registry. Participant is an institution role label, not an authenticated principal.

`data.requirements` contains `currency`, `direction` (`credit` or `debit`), positive `amount`, `urgency` (`instant`, `same-day`, `scheduled`), `availability` (`24x7`, `business-hours`), `payer_location`, `payee_location`, `return_need` (`none`, `best-effort-recovery`, `refund-rights-review`) and `source_ids`. Declare `intent_evidence_available` for a credit or `mandate_evidence_available` for a debit; exact evidence is checked by initiation review. The declaration is a design dependency, not authorization.

`candidate_profile_ids` selects native profiles. For each candidate optionally provide:

- `access_evidence`: one row with `profile_id`, `participant`, `contracted`, `reachable`, exact payer/payee locations and sources. Both booleans must be true to establish declared access/reach.
- `timing_evidence`: one row with profile/participant, `required_urgency`, `delivery_compatible`, `cutoff_and_calendar_checked`, sources. Both booleans true establish a declared SLA/calendar match; no live availability test occurs.
- `funding_evidence`: profile/participant, currency, `arrangement`, `available_amount`, sources. Balance must cover the requested amount. Even when complete, this free-text arrangement is `declared-only`; an institutional specialist must compare it with the native funding mechanism. The helper does not classify or validate funding arrangements from prose.
- `costs`: profile, currency, `per_payment_fee`, `fixed_monthly_fee`, sources. Both explicit amounts are needed; neither is inferred.

Duplicate candidate evidence leaves that criterion unknown. The result contains the full criteria matrix, native finality/return/funding/access facts and source URLs, actual supplied costs or null, and a stage/artifact workflow. `preferred_profile_id` remains null: a source-backed comparison does not infer a binding commercial choice.
