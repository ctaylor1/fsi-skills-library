# Handoffs — Insurance Fraud Referral Review

Human SIU intake evaluates the draft and counterevidence. `claim-file-quality-reviewer` can review native file-quality inputs; `subrogation-opportunity-screener` handles independently supported recovery signals. No report is submitted by this skill.

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
