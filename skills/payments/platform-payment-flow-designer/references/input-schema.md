# Native input contract

Common envelope: schema_version "1.0", request_id, as_of ISO date, jurisdiction US|EA|UK, participant, sources[] with source_id/reference/as_of/optional review_due, upstream_issues[] with code/message/optional source_ids, and data. Only analyze/draft requested_action is allowed. All amounts are nonnegative finite decimal strings or integer values; unknown values are null/omitted and remain unknown. Negative net positions are output results, not negative source transactions. Arrays must be present, including explicit empty arrays for confirmed no activity. Every native row includes source_ids registered in the envelope; primary row IDs must be unique.

`data.model`: marketplace|payfac|merchant-of-record|vertical-saas. `ledger_complete`: boolean.
- `entities[]`: entity_id, legal_name, role, source_ids.
- `accounts[]`: account_id, owner_entity_id, currency, custody_role, source_ids.
- `responsibilities[]`: activity (seller-onboarding/customer-contract/refunds/chargebacks/payouts/safeguarding-assessment), entity_id, contract_ref, source_ids.
- `charges[]`: charge_id, customer_contract_entity_id, collecting_account_id, currency, state (settled/pending/unknown), amount, source_ids.
- `allocations[]`: allocation_id, charge_id, beneficiary_entity_id, currency, type (seller/platform-fee/processor-fee), amount, source_ids.
- `adjustments[]`: adjustment_id, allocation_id, currency, type (refund/chargeback/reserve), amount, source_ids. Refund/chargeback values are cumulative financial offsets; reserve is the current outstanding hold, not cumulative hold events.
- `payouts[]`: payout_id, allocation_id, destination_account_id, currency, state (paid/pending/proposed), amount, source_ids.
Output: role_and_responsibility_map, account_ownership, charge_reconciliation and allocation_positions. No aggregate cross-entity/currency capacity exists.

For a runnable native example, see the package evals/files/request.json. Outputs retain the original source snapshot and deterministic input hash.
