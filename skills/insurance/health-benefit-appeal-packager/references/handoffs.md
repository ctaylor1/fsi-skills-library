# Handoffs — Health Benefit Appeal Packaging

The member/authorized advocate, plan review channel and appropriate clinician/legal adviser review the package. `claim-intake-preparer` legacy inputs are not a carrier adjudication handoff; intake preparation requires a new role-appropriate native input. Do not route member-side appeal facts to insurer fraud/authority workflows without explicit role and purpose authorization.

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
