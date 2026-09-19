# Data reconciliation controls

R2, read-only analysis of supplied snapshots. No source correction, assumption/method selection, actuarial certification or external mutation is implemented.

- Reject malformed keys, nonfinite values and booleans before calculating.
- Preserve duplicate ambiguity on both sides; never silently overwrite prior observations.
- Require matching financial/definition/date bases before reporting movement.
- Do not report clean when prior/expected-period checks or context/provenance are incomplete.
- Reconcile break counts, retain citations and preserve unresolved issues in the artifact.
- Compare output with the original input through `validate(output, input_doc)` when the input is available; an output-only hash check cannot independently prove a calculation.

Content fingerprints bind supplied JSON; they are not approvals, authentication or proof of an external system's state. Regex wording screens are supplementary checks, not a security or authorization boundary. Read [insurance-contract.md](insurance-contract.md).
