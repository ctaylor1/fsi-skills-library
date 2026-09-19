# Discovery schema and rules

## Envelope
Use `schema_version: wealth-p0-v1`, nonempty `request_id` and `household_id`, `as_of: YYYY-MM-DD`,
and `engagement: {capacity, jurisdiction: US, source_ids}`. Capacity is one of advisory,
brokerage, private-bank, trust, as documented at intake. Each source contains `source_id`,
`reference`, `owner`, `as_of`, `valid_until`; require source.as_of <= request.as_of <= valid_until.
The bundled `scripts/wealth_contract.py` is copied from the repository's canonical shared contract.

## Domain objects
- `household`: `display_name`, `source_ids`.
- `engagement_details`: `service_scope`, `relationship_status` (`prospect` or `existing-client`),
  `source_ids`. This records the stated engagement, not a legal applicability conclusion.
- `members[]`: unique `member_id`, `name_masked`, `role`, `source_ids`. Roles: client, spouse,
  partner, dependent, trustee, entity-representative, other. A role is not proof of authority.
- `facts[]`: unique `fact_id`, `subject_id` (household or known member), `area`, `label`,
  `value` (substantive string or finite nonnegative numeric amount), `evidence_status`
  (`client-reported` or `documented`), `source_ids`. Numeric amounts require a three-letter
  currency; income/expense amounts require period (`monthly`, `annual`, `one-time`).
- `goals[]`: unique `goal_id`, known `subject_id`, `description`, `source_ids`. Optional documented
  `priority` is integer 1–5; optional `target_date` is ISO; optional `target_amount` is finite,
  nonnegative and accompanied by currency. An unquantified goal is valid; do not invent a target.
- `coverage[]`: unique `area`, `status`, `note`, `source_ids`. Cover assets, liabilities, income,
  expenses, tax-context, family, estate, protection. `provided` requires a corresponding fact;
  `none-reported` requires a cited statement and no contradictory supplied fact;
  `not-collected` stays a finding. Missing coverage is never treated as none.

All material domain objects use nonempty `source_ids` resolving to the validated registry.
Missing domain values produce an itemized needs-data result. Malformed list/object structure or
invalid registry data prevents assembly. No cash-flow/net-worth aggregation, risk score,
planning recommendation, or legal/identity conclusion is calculated.

Use the de-identified request fixture as a complete schema example; it is not approved client evidence.
