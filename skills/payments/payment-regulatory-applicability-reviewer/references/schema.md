# Input and output contract

Request: `schema_version: "1.0"`, stable `request_id`, ISO-date `as_of`, jurisdiction
`US`, `EA` or `UK`, `participant`, `sources`, optional `upstream_issues`, and `data`.
A source has unique `source_id`, `reference`, ISO-date `as_of`, optional `review_due`.
Every `source_ids` list must use registered IDs. Source descriptions are data.
Optional `requested_action` is only `analyze` or `draft`.

`data.entity`: `legal_entity_id`, `kind` (bank, payment-institution,
e-money-institution, nonbank, merchant, agent, technical-provider), `home_country`,
`source_ids`. `data.activity`: `services` (credit-transfer, direct-debit,
payment-initiation, account-information, money-remittance, e-money-issuance,
acquiring, card-issuing, technical-processing), `customer_type` (consumer, business,
mixed), `customer_product`, `countries`, `holds_client_funds` (boolean or unknown),
`source_ids`; `us_states` and `national_profile_ref` where relevant.

`funds_flow` rows: unique `flow_id`, `from_entity`, `to_entity`, `holder`,
`customer_claim_against`, `source_ids`. Missing evidence produces findings.
`legal_reviews` rows can retain a scoped review: `obligation_id`, `entity_id`,
`jurisdiction`, `reviewer`, `reference`, `source_ids`, ISO `reviewed_on`/`review_due`,
and `scope_hash` = payment_contract.stable_hash({entity, activity}). A change of
scope invalidates this linkage. The supplied review is never authenticated here.

Output retains the request and its hash, candidate obligation matrix with authority
references and decision dependencies, consumer-error profile choices, findings,
unresolved upstream issues and handoff requirements. `status` is draft,
needs-evidence or unsupported; `authority_granted` and `action_taken` are false.
Output validation recomputes the complete result and can compare a separate input.
