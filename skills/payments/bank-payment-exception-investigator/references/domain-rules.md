# Casework rules

Build chronology using timezone-aware ordering. Retain source references and the reported last status; do not infer legal finality from it. Supplied party/amount fields are carried into an evidence bundle and are not independently resolved.

1. Missing message/identifier evidence → `needs-data`.
2. Explicit fraud indicators → fraud investigation; explicit sanctions hold → sanctions adjudication. `RR04` alone → obtain regulatory-cause information, not a sanctions match assertion.
3. Match to a supplied open case → possible duplicate; link for owner confirmation without merging.
4. Recall → recommend an information request unless cited scheme eligibility, current finality/window, funds availability and required consent are present. Even an honor recommendation does not establish recovery or authorize a response.
5. A repair/return reason code provides a candidate operation only. Cited eligibility is required before an operation recommendation. Field repair also requires a confirmed defect, verified correction, and not-settled state.
6. Otherwise request information. Missing consent is not automatically a final rejection decision.

Generated `PEI-<exception_id>` values are local report references, never proof that a case was opened. Existing case IDs and owners are supplied metadata. Unassigned ownership remains explicit. Priority is illustrative and must not hide fraud/hold flags; no mixed-currency nominal threshold comparison is permitted.
