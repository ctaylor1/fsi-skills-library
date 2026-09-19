# Input and source contract

The common `wealth-p0-v1` envelope requires nonempty `request_id`, `household_id`, ISO-date
`as_of`, `engagement` with capacity advisory/brokerage/private-bank/trust and jurisdiction US,
and `sources[]` with source_id, reference, owner, as_of and valid_until. Source observations
cannot postdate the request or expire before it. Registry metadata is user-supplied evidence,
not independently authenticated approval. Unknown item source IDs create needs-data.

Domain records (each material record includes `source_ids[]`):
- `client`: integer age 0–125 when known; human-recorded boolean impairment_flag when known.
- `history_coverage`: start/end ISO dates establishing requested history coverage.
- `transactions[]`: unique txn_id, ISO date/timestamp, finite nonnegative amount, debit/credit,
  normalized counterparty, explicit lifecycle executed/proposed/pending/cancelled, source_ids.
  For executed rows, date is the execution timestamp; for proposed/pending rows, date is the
  request/observation timestamp, not a claimed future execution. `focal_txn_ids[]` must resolve
  uniquely to executed/proposed/pending activity. Cancelled rows may be supporting history.
  Missing lifecycle is rejected; adapters must never assume a proposed request executed.
- `lookback_days`: integer requested history length; window-only mode is unsupported.
- `config`: version, owner, engagement-matching capacity/jurisdiction, numeric parameters in
  domain-rules and source_ids. No synthetic fixture value is a production default.
- `trusted_contact`: on_file boolean; last_confirmed when present; collection_status
  declined/requested/not-requested when absent. Missing data is not a breach determination.
- `recent_changes[]`: type beneficiary/registration/address, date and source_ids. Empty list
  declares no changes in the supplied coverage; omitted list means unknown.
- `observations`: observed_by (trained-human reference), source_ids; nullable booleans for
  third_party_present, new_caregiver_or_poa, confusion_observed, cannot_recall_transaction,
  repeated_questions, unusual_urgency, requests_secrecy, refuses_family_involvement,
  scam_narrative_flag. Unknown and false are different values.

The source hierarchy is transaction record, sourced CRM observation/context, and reviewed
policy configuration. Keep conflicting facts visible; do not substitute an agent inference.
Connectors, permission checks, actual completeness and policy approval are deployment work.
The output's digest covers the entire input snapshot; it is an identity check, not a signature
or authorization token. Keep snapshot access no broader than source access.
