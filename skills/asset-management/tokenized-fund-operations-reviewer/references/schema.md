# Native schema

Use foundation request_id, object_id, as_of, knowledge_cutoff, currency, audience=`internal-review`, sources and optional unresolved_issues. Currency is the share-class reporting denomination, not a conversion instruction. Domain rows have unique IDs and registered source_ref. Collections are explicit, at most 10,000 rows; register/wallet/permission inventories are nonempty. Beneficial records/transfers may be empty. Numbers use finite decimals under the foundation 38-digit/exponent bounds; token atoms/counts must be integral.

| Object / row | Required fields |
| --- | --- |
| fund | fund_id equal to object_id, share_class_id, owner, legal_register_basis, registry_snapshot_id, observed_on=as_of, legal_unit_decimals/token_decimals integers 0..18, positive tokens_per_legal_unit, nonnegative official_issued_units, source_ref |
| ledger | snapshot_id, network_id, contract_id, block_id, observed_on=as_of, total_token_atoms, finality_status final/pending/reorged/unknown, confirmations integer, reorg_detected boolean, source_ref; finality_policy has version, reviewer, minimum_confirmations integer, source_ref |
| register / legal_account_id | account_type direct/omnibus, snapshot_id matching fund, holder_identity, fund_id, share_class_id, legal_units |
| wallets / wallet_id | legal_account_id, snapshot_id/network_id/contract_id matching ledger, custody_owner, token_atoms |
| beneficial_register / record_id | omnibus_account_id, beneficial_holder_id, register snapshot_id, legal_units; each omnibus/beneficial-holder pair unique |
| transfer_permissions / permission_id | wallet_id, matching legal_account_id, policy_version, eligible/frozen booleans, observed_on; one observation per wallet |
| transfers / transfer_id | from_wallet, to_wallet (distinct), ledger snapshot_id, positive token_atoms, status finalized/pending/reversed/reorged, included_in_snapshot boolean, observed_on equal to snapshot date |

Legal units must fit declared precision. Expected atoms=legal units times tokens_per_legal_unit times 10^token_decimals; any fractional atom is rejected. No rounding, fee conversion or token rebasing occurs. All balances are for one fund/share class and one network/contract. Multiple networks, bridged/wrapped representations and intraday event reconstruction require a separate reviewed method.

Results reconcile fund totals, each legal account's token atoms and each omnibus subregister, with explicit atomic differences. Current supplied eligibility/freeze records inform transfer findings. Transfers are reviewed as observations and never replayed into balances. confirmed_reconciled is false if finality or any evidence issue remains. It refers only to supplied reconciled records, never source authenticity, legal title or network control. Full output validation reconstructs from the detached original.
