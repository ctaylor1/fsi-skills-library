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

## Card-lifecycle data

`account`: account_id, state, source_ids. `cards`: card_id, account_id, state,
optional replaces_card_id, source_ids. `tokens`: token_id, card_id, state, source_ids.
Opaque references only; never PAN or authentication data.

`transactions`: transaction_id, account_id, card_id, currency, events, source_ids.
Each event: event_id, kind, timestamp with UTC offset, source_system,
source_record_id, source_ids; monetary events also amount (decimal string) and currency.
Kinds: authorization, hold, hold-release, authorization-reversal,
authorization-expiry, presentment, presentment-reversal, clearing, settlement,
funding, posting, refund. Authorization has outcome; hold/presentment/reversal/expiry
use authorization_id. Hold release has hold_id; presentment reversal has presentment_id.
IDs refer to events in the same transaction. An unsupported kind is a coverage gap.

`profile`: shared declared rule-profile fields (profile_id, version, source_ref,
authority, review_owner, status active, effective_from, optional effective_to,
review_due, participants, jurisdictions), source_ids, `multiple_presentments` and
`release_hold_on_presentment` booleans, and `source_authorities`, mapping lifecycle
stage to source-system names. Missing profile data is a gap, not an invented rule.
`operation`: optional type, scoped card/account/transaction references and source_ids.

Result keeps account/card/token states, transaction assessments, stage amounts,
profile issues and controlled action requirements. `remaining_hold_scenario` can be
null. `completion_or_funds_availability_verified` is always false. Native ISO 8583,
network files and token-service adapters are not bundled: supply normalized events.
See [../evals/files/normal.json](../evals/files/normal.json) for synthetic input.
