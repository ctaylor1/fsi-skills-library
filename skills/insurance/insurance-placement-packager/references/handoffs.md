# Ownership and handoff

- `insurance-submission-preparer` supplies reconciled intake; the receiver still needs native placement identity, response terms, dates and sources.
- `premium-quote-comparator` owns a narrower premium comparison; `policy-wording-comparator` owns detailed clause deltas and `coverage-gap-analyzer` owns prospective needs-versus-coverage analysis.
- `insurance-producer-onboarding-reviewer` reviews credentials; `insurance-delegated-authority-reviewer` reviews an actual delegation. Neither is binding execution.

A handoff contains case/object/party/capacity, as_of, source versions, findings, unresolved issues and the source artifact. Adapt those facts to the receiver’s native schema and run its actual input validator. A common envelope is not field compatibility or access permission. If a destination is unavailable, disclose the capability gap and retain the packet for a human owner.
