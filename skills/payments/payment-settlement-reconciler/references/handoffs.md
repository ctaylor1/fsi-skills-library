# Settlement handoffs and mode ownership

The package owns both payout report normalization (explain-payout) and scoped settlement
comparison (reconcile-settlement). Reuse an existing report snapshot with the same content
hash and scope; do not create an additional summarizer execution.

Transaction/order matching goes to payment-transaction-reconciler. Full exception chronology
goes to bank-payment-exception-investigator with source references, partition, checks and unresolved
issues. Interpretation of camt/pacs fields goes to iso-20022-message-interpreter. Fee advice
goes to merchant-payment-cost-analyzer; a chargeback shown in a report routes to the merchant dispute
evidence workflow. General ledger analysis goes to gl-reconciler and requires independent
booking evidence; no discrepancy in this package is itself a proposed journal.

Machine-readable investigation handoffs use bundled payment contract version, stable ID,
source/target skills, case ID, lead owner, requested output, source refs, unresolved issues
and target_input. action_mode is read-only, target_validation is required and
authority_granted is false. The target must map and validate its own input independently.
A handoff cannot authorize posting, payment repair, communication or a system state change.

Phase 1 handoff: retain case/participant/rail/jurisdiction, original source references and unresolved issues using payment-contract.md. Validate the target native input independently; renamed skills are not assumed input-compatible. Local IDs and hashes grant no authority and do not persist or accept a case. Only invoke installed capabilities within the requested scope.
