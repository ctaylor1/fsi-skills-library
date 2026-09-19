# Native input contract

Common envelope: schema_version "1.0", request_id, as_of ISO date, jurisdiction US|EA|UK, participant, sources[] with source_id/reference/as_of/optional review_due, upstream_issues[] with code/message/optional source_ids, and data. Only analyze/draft requested_action is allowed. All amounts are nonnegative finite decimal strings or integer values; unknown values are null/omitted and remain unknown. Negative net positions are output results, not negative source transactions. Arrays must be present, including explicit empty arrays for confirmed no activity. Every native row includes source_ids registered in the envelope; primary row IDs must be unique.

`data.history_complete`: boolean. `approval_policy`: owner, policy_ref, effective_from, review_due (ISO dates).
- `suppliers[]`: supplier_id, legal_entity_id, payee_account_ref, erp_supplier_ref, enabled_methods[], source_ids.
- `invoices[]`: invoice_id, invoice_number, supplier_id, buyer_entity_id, currency, erp_invoice_ref, due_date, amount, source_ids.
- `credit_notes[]`: credit_note_id, invoice_id, currency, erp_credit_ref, amount, source_ids.
- `payments[]`: payment_id, supplier_id, payer_entity_id, payee_account_ref, currency, method, state (settled/pending/proposed/unknown), erp_payment_ref, amount, source_ids.
- `allocations[]`: allocation_id, payment_id, invoice_id, currency, amount, source_ids.
- `remittances[]`: remittance_id, payment_id, supplier_id, delivery_reference, allocation_ids[], source_ids. Allocation IDs must match every allocation for that payment exactly once.
Output: invoice_balances, payment_remittance_ties, supplier_enablement and ERP workflow. Remaining-before-proposed values are unknown on incomplete/conflicting history.

For a runnable native example, see the package evals/files/request.json. Outputs retain the original source snapshot and deterministic input hash.
