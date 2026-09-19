# Ownership and handoff

`insurance-data-reconciler` resolves source ledger mismatches; `insurance-premium-billing-reconciler` owns billed receivables after human audit approval; `insurance-underwriting-risk-reviewer` owns risk review. Do not use this for policy pricing recommendations or automatic class reassignment.

Transmit only a draft artifact in an authorized channel: durable case ID, original capacity/party/object, as_of, source versions, method profile, native results, unresolved issues and source envelope. Map the actual receiving native data fields and run that receiver's input validator; envelope validity is not schema compatibility. A role change requires a reviewed source-bound context mapping and never erases upstream issues. If the receiver is unavailable, preserve the draft and name the human owner; never pretend a handoff completed.
