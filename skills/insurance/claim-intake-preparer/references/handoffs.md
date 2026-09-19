# Handoffs — Claim Intake Preparation

`claims-triage-assistant`: pass the reviewed normalized fields only after an explicit assigned claim ID and reviewed claim-type mapping exist. Validate its native as_of/config_version/claims schema; do not rename FNOL ID into claim ID automatically. `claim-cost-reconciler` and `liability-evidence-matrix-builder`: separately supply their document/line-item or fact/evidence schemas.

## Review handoff contract
Use a versioned insurance handoff only after constructing the receiving package’s native input.
Retain upstream artifact, source versions and unresolved issues; request an explicit output.
Run the actual receiver validate_input function through validate_handoff before presenting it
as consumable. Similar field names or artifact IDs alone do not establish compatibility.
No handoff grants execution authority or silently changes capacity or represented party.

## Revisions and duplicate work
Use artifact_hash for a specific revision and retain input_hash/output_hash. Human-readable IDs
are labels and may recur across revised calculations. Recalculation or a routing suggestion
is not submission, delivery, approval, payment or proof of completed downstream work.
