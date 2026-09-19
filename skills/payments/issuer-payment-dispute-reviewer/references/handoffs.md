# Handoffs

Merchant/acquirer representment → `merchant-chargeback-response-packager`. Fraud/scam investigations are consultations to `payment-fraud-and-scam-investigator`, returning evidence without extinguishing issuer deadlines. Payment exceptions → `bank-payment-exception-investigator`; reconciliation → `payment-transaction-reconciler` / `payment-settlement-reconciler`. Human issuer personnel own adjudication, provisional/final credit, notices, filing and closure.

Preserve source case/transaction IDs, original evidence and unresolved issues. Use the [payments contract](payment-contract.md) envelope for actual transfers; consultation descriptors in this package are requests, not proof of target execution. Target-native validation is required. The lead retains ownership until a handoff is accepted.

Phase 1 handoff: retain case/participant/rail/jurisdiction, original source references and unresolved issues using payment-contract.md. Validate the target native input independently; renamed skills are not assumed input-compatible. Local IDs and hashes grant no authority and do not persist or accept a case. Only invoke installed capabilities within the requested scope.
