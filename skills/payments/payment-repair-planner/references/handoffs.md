# Repair-planning handoffs

A confirmed bank exception can enter directly or from `bank-payment-exception-investigator`. The receiving planner must validate its full own schema; an upstream case ID and a proposed disposition are insufficient.

Unconfirmed cause → bank exception investigation. Fraud indicators → payment fraud casework. Uncleared screening → the authorized sanctions/compliance owner. Unavailable or out-of-scope policy → the policy owner. Settlement discrepancies → payment settlement/transaction reconciliation.

Outputs are reviewable offline proposals only. Do not route an execution request back into this planner as though a token enabled writes. Hold release and ordinary returns/refunds/cancellations need a servicing workflow; settlement is never undone by changing this plan.

For structured transport, use [payment-contract.md](payment-contract.md) with requested output `offline field-repair proposal`, `authority_granted: false`, and independent target validation. Preserve case ownership and unresolved prerequisites until accepted by the receiving owner.

Phase 1 handoff: retain case/participant/rail/jurisdiction, original source references and unresolved issues using payment-contract.md. Validate the target native input independently; renamed skills are not assumed input-compatible. Local IDs and hashes grant no authority and do not persist or accept a case. Only invoke installed capabilities within the requested scope.
