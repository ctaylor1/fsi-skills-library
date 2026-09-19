# Handoffs

Issuer customer error, unauthorized-transfer or billing-error review → `issuer-payment-dispute-reviewer`. Merchant and acquirer representment remain here. Fraud/scam evidence → `payment-fraud-and-scam-investigator`; scheme changes → `payment-scheme-change-tracker`; settlement/ledger breaks → `payment-settlement-reconciler` / `payment-transaction-reconciler`. A scheme-change alert is not itself a current operating rulebook.

Preserve source case/transaction IDs, original evidence and unresolved issues. Use the [payments contract](payment-contract.md) envelope for actual transfers; consultation descriptors in this package are requests, not proof of target execution. Target-native validation is required. The lead retains ownership until a handoff is accepted.

Phase 1 handoff: retain case/participant/rail/jurisdiction, original source references and unresolved issues using payment-contract.md. Validate the target native input independently; renamed skills are not assumed input-compatible. Local IDs and hashes grant no authority and do not persist or accept a case. Only invoke installed capabilities within the requested scope.
