# Readiness rules

Each required item must have one unambiguous attestation. Missing, unknown or duplicate
states remain gaps. A supplied evidence pointer does not satisfy an item. A declared
inspection requires evidence_review {status: inspected, reviewer, reviewed_at, scope,
result_ref}; the tool checks those declarations, not the external evidence or identity.
N/A remains an applicability-review gap in this bounded engine, including a manual
alternative control. No universal checklist or go-live decision is inferred.

Score = declared inspected items / required items. Empty checklists yield zero, not
readiness. ready-for-review means no gaps in the supplied checklist only. A production
approver must independently assess completeness, outcomes, applicability and authority.
