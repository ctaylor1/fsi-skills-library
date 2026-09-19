# Optional composition

- `payment-lifecycle-diagnoser`: use when the job spans multiple events/attempts rather than one message.
- `bank-payment-exception-investigator`: use for a bank investigation chronology, ownership and conditional recommendation.
- `payment-repair-planner`: use only for a confirmed defect with exact correction, policy and screening evidence; it drafts an offline plan.
- Account-reporting/settlement reconciliation: classification-only camt output is not a normalized ledger or settlement dataset. A suitable extraction adapter and the reconciliation input contract are still required.

A raw XML request requires a separately available parser; this package must disclose that it cannot supply one. Recognized camt.110/111/admi.024 names are useful routing context, not completed case-message interpretation.

Use [payment-contract.md](payment-contract.md) for a handoff envelope, preserve the lead owner and source references, and require target validation. No fixed serial pipeline is required; the user can enter any workflow directly with sufficient evidence.

Phase 1 handoff: retain case/participant/rail/jurisdiction, original source references and unresolved issues using payment-contract.md. Validate the target native input independently; renamed skills are not assumed input-compatible. Local IDs and hashes grant no authority and do not persist or accept a case. Only invoke installed capabilities within the requested scope.
