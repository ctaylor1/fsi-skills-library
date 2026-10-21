# Bank exception handoffs

- `payment-lifecycle-diagnoser` can provide a one-payment trace; casework may also start directly with sufficient evidence.
- `iso-20022-message-interpreter` can interpret supported normalized JSON. It cannot decode raw XML or validate arbitrary camt schemas.
- `payment-repair-planner` receives confirmed defect evidence, original snapshot, exact old/new value, scoped policy and screening bound to that proposed instruction. An investigation bundle alone does not meet the planner's schema.
- `sanctions-match-investigator` receives an actual sanctions hold/disposition question. A generic regulatory reason requires clarification first.
- `payment-fraud-and-scam-investigator` receives fraud-indicator evidence, not a pre-decided outcome.
- Merchant funding holds and payout/cash breaks route to settlement reconciliation and merchant-risk review. Native ACH requires a dedicated adapter before this case builder can process its records.

No executor is provided by this package or by the repair planner. Returns, recall responses, and hold releases remain with authorized operational systems and their human controls. Preserve one lead owner and require receiving-target validation and acceptance; see [payment-contract.md](payment-contract.md). Do not turn these options into a mandatory serial pipeline.

Phase 1 handoff: retain case/participant/rail/jurisdiction, original source references and unresolved issues using payment-contract.md. Validate the target native input independently; renamed skills are not assumed input-compatible. Local IDs and hashes grant no authority and do not persist or accept a case. Only invoke installed capabilities within the requested scope.
