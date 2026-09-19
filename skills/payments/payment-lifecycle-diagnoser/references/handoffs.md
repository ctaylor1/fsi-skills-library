# Handoffs

| Condition | Destination | Required handoff evidence |
|---|---|---|
| Ambiguous or failed bank payment | `bank-payment-exception-investigator` | Case owner, payment/attempt identity, source trace, unresolved issues; target's normalized case schema must be assembled and validated |
| Specific normalized ISO message | `iso-20022-message-interpreter` | Supported normalized profile, cited message and supplied guideline metadata |
| Fraud indicator | `payment-fraud-and-scam-investigator` | Indicator evidence without a fraud conclusion |
| Unauthorized return or disputed transaction | Available issuer-dispute workflow | Rail, participant role, consumer/business context; no automatic card-chargeback treatment |
| Card operational ambiguity | Human `payment-operations-review` queue | Attempt trace, duplicate exposure, unresolved settlement |

A diagnostic pack is not automatically valid target input. Use the shared handoff envelope in [payment-contract.md](payment-contract.md), then run the target input validator. Preserve the lead owner until the receiver accepts the handoff. Do not invent an installed skill for a human queue.

A repair plan requires a confirmed exception, exact correction, screening scope, and policy evidence. This skill does not bypass those prerequisites. Direct casework or interpretation entry is valid when the user already supplied complete evidence.

Phase 1 handoff: retain case/participant/rail/jurisdiction, original source references and unresolved issues using payment-contract.md. Validate the target native input independently; renamed skills are not assumed input-compatible. Local IDs and hashes grant no authority and do not persist or accept a case. Only invoke installed capabilities within the requested scope.
