# Advanced platform optional native schema

Use the core envelope and all fields from input-schema.md. This module has separate CLIs and no effect on ordinary requests. Preserve all original arrays and row source_ids.

Additional fields:
- connections[]: connected_id, owner_entity_id, account_id, optional parent_connected_id, agreement_ref, refund_owner_ref, chargeback_owner_ref, source_ids. Accounts cannot be reused across connection IDs. Parents do not own child accounts automatically.
- allocations[] additionally connected_id, optional parent_allocation_id, and transfer_agreement_ref when parent and child beneficiaries differ. Trees conserve each charge at roots and every split at internal nodes. Child charge/currency must exactly match parent; connected hierarchy must match allocation hierarchy. Residual retained shares must be explicit leaves. Only leaf allocations may receive adjustments or payouts.
- adjustments[] and payouts[] additionally economic_id, globally unique across both collections. Supply a canonical economic segment rather than multiple processing states for the same segment. A genuine split event requires separately reconciled segment identities; the helper cannot authenticate a relabelled duplicate.
- batches[]: batch_id, owner_entity_id, currency, contract_ref, payout_ids[], source_ids. Every payout appears exactly once, with no duplicate or unknown ID. Each batch has one beneficiary entity and currency. Historical, pending and proposed entries remain separately staged by the underlying payout records; nominal batch total is not cash released.

The helper flattens verified leaves into the preserved core reconciler. Any hierarchy, ownership, batch or identity gap suppresses capacity. Internal nodes never add money to leaf totals. Complete history, settled collection and exact destination owner/currency remain required. Connection labels and supplier contracts are evidence references, not identity or legal verification. Cross-border, FX and inter-entity netting are out of scope.
