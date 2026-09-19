# Ownership and handoff

`insurance-producer-onboarding-reviewer` owns credential/appointment evidence; `insurance-data-reconciler` owns record breaks; `insurance-premium-billing-reconciler` owns premium receivables. Send credential questions back to onboarding and compensation arithmetic here; do not turn one into the other.

Transmit only a draft artifact in an authorized channel: durable case ID, original capacity/party/object, as_of, source versions, method profile, native results, unresolved issues and source envelope. Map the actual receiving native data fields and run that receiver's input validator; envelope validity is not schema compatibility. A role change requires a reviewed source-bound context mapping and never erases upstream issues. If the receiver is unavailable, preserve the draft and name the human owner; never pretend a handoff completed.
