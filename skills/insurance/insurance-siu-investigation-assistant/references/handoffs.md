# Ownership and handoff

`insurance-fraud-referral-reviewer` owns initial signal triage; `claim-coverage-reviewer` owns carrier denial review; `claimant-dispute-packager` owns claimant advocacy. Triage referral plus bounded question comes here; insufficient signals return to triage. A hypothesis is not a fraud determination or authority for a denial.

Transmit only a draft artifact in an authorized channel: durable case ID, original capacity/party/object, as_of, source versions, method profile, native results, unresolved issues and source envelope. Map the actual receiving native data fields and run that receiver's input validator; envelope validity is not schema compatibility. A role change requires a reviewed source-bound context mapping and never erases upstream issues. If the receiver is unavailable, preserve the draft and name the human owner; never pretend a handoff completed.
