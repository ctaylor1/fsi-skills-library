# Servicing contract

Use [input-schema.json](input-schema.json) and `evals/files/normal.json`. The example policy and deadline are synthetic. All evidence carries registered `source_ids`; money is a positive decimal string and explicit currency.

`data.original_payment`: payment ID, `state` (`draft`, `authorized`, `submitted`, `accepted`, `settled`, `posted`, `rejected`, `returned`, `unknown`), amount/currency, rail profile ID, originator and beneficiary account refs, sources. `authorized` and `accepted` are not settlement evidence.

`service_request`: unique service ID, original payment ID, `action` (`refund`, `void`, `reversal`, `return`, `cancel-recovery`), amount/currency, reason, destination account ref for funds movements, sources. `original_binding` exactly repeats original payment ID, state, amount, currency, rail and both account refs, plus card family/network/product when present. A changed snapshot requires a new binding. Optional `requested_effect: rollback` is explicitly unsupported. `authority_source: repair` cannot establish servicing authority.

`prior_services`: complete ledger rows with unique service ID, original payment ID, action, amount/currency, status (`completed`, `pending`, `failed`, `cancelled`), sources. Declare `prior_service_ledger_complete: true` explicitly. Completed and pending amounts both reserve remaining capacity; cancelled/failed amounts do not. Missing/inconsistent ledger means unknown capacity, not a zero-history assumption.

`policy`: jurisdiction, participants, profile IDs, active `effective_from`/`effective_until`, `revoked: false`, approval roles and sources. Its `permissions` list contains action, currency, supported `original_states`, `max_amount`, reviewed `deadline_date` and sources. The adapter compares a supplied date; it does not calculate statutory, business-day or scheme clocks. One applicable permission is required.

Bank rail ID must resolve to a currently reviewed native profile for jurisdiction and currency. Cards require original `rail_family: card`, `network`, `product` and matching policy values plus `card_profile`: exact profile ID/network/product, jurisdiction, participants, allowed actions, source version, effective dates/revocation, reviewed-on/review-due dates and sources. Provider rule facts remain supplied and need independent specialist review.

Output binds the original snapshot, requested service, remaining capacity, expected financial effect, approval roles and required post-action evidence. `execution_authorized` and `original_ledger_rolled_back` are always false. A request's financial effect stays unknown until actual response and funds-movement evidence arrive.
