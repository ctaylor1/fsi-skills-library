# Controls

Risk R3; action mode draft-only. Human approval: required. No posting, submission, payment initiation, payout, settlement, system-of-record update, beneficiary change, limit change or approval authority. Do not infer permission from a valid input, balanced ledger, linked contract, known account, model label or successful helper execution.

States: triage -> source validation -> draft/needs-evidence/unsupported -> owner review -> separate authorized downstream process. Preserve request_id and source snapshot; never mark a case closed or a customer paid. Missing/ambiguous amounts and history remain unknown. Cross-entity/currency evidence is never pooled. A reviewer can correct and resubmit the source request; editing an output fails recomputation.

Maintain separation between preparer, reviewer and production execution owner. Escalate unknown outcomes, duplicate identifiers, mismatched owners, stale rules and insufficient capacity. Preserve upstream gaps in every handoff. Protect payment/ERP/treasury records under role-based access and approved retention. No external delivery is performed by these scripts. Human acceptance, connector identity and production control testing remain separate gates.
