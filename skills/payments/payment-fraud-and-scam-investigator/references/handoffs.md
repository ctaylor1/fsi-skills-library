# Handoffs

`instant-payment-risk-monitor` can supply alerts. `phishing-and-bec-investigator` examines email artifacts only; return evidence here. Sanctions match → `sanctions-match-investigator`; adverse media → `adverse-media-investigator`; suspicious patterns → AML triage/investigation. Keep restricted financial-crime evidence appropriately scoped. Issuer statutory redress → `issuer-payment-dispute-reviewer`; merchant/acquirer dispute response → `merchant-chargeback-response-packager`; operational repair planning → `payment-repair-planner`. A handoff is a review request, not execution authority.

Preserve source case/transaction IDs, original evidence and unresolved issues. Use the [payments contract](payment-contract.md) envelope for actual transfers; consultation descriptors in this package are requests, not proof of target execution. Target-native validation is required. The lead retains ownership until a handoff is accepted.

Phase 1 handoff: retain case/participant/rail/jurisdiction, original source references and unresolved issues using payment-contract.md. Validate the target native input independently; renamed skills are not assumed input-compatible. Local IDs and hashes grant no authority and do not persist or accept a case. Only invoke installed capabilities within the requested scope.
