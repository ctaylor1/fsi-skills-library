# Settlement and explanation controls

The package's maximum risk tier is R2 for reconciliation; explain-payout is informational
read-only analysis. It does not select a legal owner of unexplained funds or produce
accounting corrections. Any journal analysis requires independent accounting policy,
chart-of-accounts mapping, source investigation and an authorized downstream process.

No bundled command posts journals, writes business systems, resubmits payments, sends
messages or closes cases. External delivery requires the reviewer's authorization.
Investigation handoffs have authority_granted=false and require independent target validation.

Input snapshots and hashes support reproducibility, not authentication. Citations remain
supplied evidence. Use masked, minimized inputs; never include PAN, sensitive authentication
data, secrets or unnecessary customer records. Preserve dates, partitions, configuration
versions and evidence under deployment retention policy.

Fail on malformed/nonfinite/boolean amounts and invalid required scope. Accept missing
amounts as unknown and discrepant reports as useful analytical inputs. Never manufacture a
zero, missing schedule rate, normal business-day delay, confirmed cash receipt or adjusting
entry. Output validators recompute all fields; include --input to bind source evidence.

Deterministic tests do not certify a live integration, legal/compliance status or real-model
workflow quality. Those require independent deployment and domain-owner review.
