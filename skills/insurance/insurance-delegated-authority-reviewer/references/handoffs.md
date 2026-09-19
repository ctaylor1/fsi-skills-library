# Ownership and handoff

- `insurance-producer-onboarding-reviewer` supplies credential evidence; this workflow independently checks the delegation and transaction.
- `insurance-placement-packager` uses the exception packet as evidence only; binding remains separate.
- `insurance-data-reconciler` owns broader record reconciliation; `insurance-underwriting-risk-reviewer` owns the risk rationale. Claims settlement authority belongs to `claim-settlement-authority-request-builder` when the actual job is a carrier claim authorization request.

A handoff contains case/object/party/capacity, as_of, source versions, findings, unresolved issues and the source artifact. Adapt those facts to the receiver’s native schema and run its actual input validator. A common envelope is not field compatibility or access permission. If a destination is unavailable, disclose the capability gap and retain the packet for a human owner.
