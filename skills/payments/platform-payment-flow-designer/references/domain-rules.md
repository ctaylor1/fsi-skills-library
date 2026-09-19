# Domain rules and limits

## Calculation contract
For allocation A: owed_after_paid = original allocation - refunds - chargebacks - paid payouts. Reserve holdings remain a liability and reduce availability, not entitlement. available_before_proposed = owed_after_paid - reserve_held - pending_payouts, only for an evidenced settled collection and complete consistent ledger. Compare all proposals for that allocation to this capacity. Fee allocations are explicit alongside seller allocations; charge gross must equal their sum. There is no currency or entity aggregation.

The input is a cumulative as-of position with unique economic records. Refund and chargeback rows must be disjoint; any recovery/reversal of either requires upstream reconciliation into the supplied net original-linked amount with source evidence. The helper does not infer whether two different source IDs represent one real-world event. It does not calculate tax, legal safeguarding, network fees or contractual reserve release conditions. Unknown links or monetary values cannot become zero. Public model labels never establish licensing, scheme registration or account access.
