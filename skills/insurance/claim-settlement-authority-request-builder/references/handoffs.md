# Handoffs — Settlement Authority Request Preparation

`liability-evidence-matrix-builder` and `claim-cost-reconciler` can supply evidence components. They do not supply a coverage determination or settlement valuation. Deliver a request to the authorized human approver only through a separately authorized execution process.

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
