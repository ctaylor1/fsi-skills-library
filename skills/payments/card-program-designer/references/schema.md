# Native request and output contract

All commands consume JSON and run locally. Input envelope: `schema_version: "1.0"`,
`request_id` (caller-provided durable work-item reference), `as_of` (YYYY-MM-DD),
`jurisdiction` (`US`, `EA`, or `UK`), `participant`, `sources`, `upstream_issues`, and
`data`. A source has `source_id`, `reference`, `as_of`, and optional `review_due`.
Use `source_ids` arrays referencing those registered IDs on all material data rows.
Missing evidence is a finding. Invalid types, unsafe actions and invented source
IDs are input errors. `requested_action` permits `analyze` or `draft` only.
An unsupported region returns `unsupported` with no jurisdiction-specific result.

The source inventory records supplied claims; it does not authenticate evidence.
A passed validator is not evidence inspection. Source review-due dates before the
analysis date create gaps. Future source dates are rejected. Raw PAN, CVV, PIN,
track data, customer secrets and payment credentials are unnecessary: use opaque
card/account/token references and synthetic or minimized business evidence.

Output contains `status` (`draft`, `needs-evidence`, `unsupported`), a retained
`source_snapshot` and `input_hash`, `result`, source-linked `findings`, `handoffs`,
upstream unresolved issues and limitations. `authority_granted` and `action_taken`
remain false. A hash establishes content lineage, never identity or approval.
Compare a saved output to separately supplied input when source binding matters.

## Card-program data

`program`: name, proposition, customer_segment (`consumer`/`commercial`), card_type
(`credit`/`debit`/`prepaid`), territories (US/EA/UK), currency, source_ids.
`parties`: party_id, name, roles (issuer/sponsor/processor/program-manager and any
additional declared roles), source_ids. Distinct IDs must identify distinct parties.
`responsibilities`: responsibility, owner_party_id, support_party_ids, source_ids.
Use the duty IDs in `scripts/domain.py`; unprovided duties remain unresolved.

`funding`: model, source_of_funds, settlement_funding_party_id, customer_funds_model,
source_ids. Credit also needs credit_risk_party_id and receivables_owner_party_id.
Debit/prepaid need custodian_party_id, account_title and insolvency_treatment.
These are proposals/declared terms, not independently authenticated legal conclusions.
`fund_flows`: flow_id, purpose, currency, from_party_id, to_party_id, trigger, source_ids.
`controls`: control_id, area, owner_party_id, design, source_ids. Review areas are
fraud, complaints-and-disputes, credential-security and financial-reconciliation.
`rewards`: offered boolean plus supplied terms. `economics`: cited assumptions only.

Result: `program`, `role_map`, `responsibility_matrix`,
`funding_and_customer_funds`, `funds_flow_blueprint`, `control_designs`,
`rewards_proposal` and `economic_assumptions`. No credit policy or profitability is
calculated. See [../evals/files/normal.json](../evals/files/normal.json) for synthetic input.
