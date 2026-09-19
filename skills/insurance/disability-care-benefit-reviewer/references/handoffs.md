# Ownership and handoff

`claimant-dispute-packager` owns a claimant appeal; `claim-coverage-reviewer` owns review of a proposed carrier denial; `claim-settlement-authority-request-builder` owns settlement authority. Route medical/vocational fact questions to the qualified human assessor, and return only their sourced assessment.

Transmit only a draft artifact in an authorized channel: durable case ID, original capacity/party/object, as_of, source versions, method profile, native results, unresolved issues and source envelope. Map the actual receiving native data fields and run that receiver's input validator; envelope validity is not schema compatibility. A role change requires a reviewed source-bound context mapping and never erases upstream issues. If the receiver is unavailable, preserve the draft and name the human owner; never pretend a handoff completed.
