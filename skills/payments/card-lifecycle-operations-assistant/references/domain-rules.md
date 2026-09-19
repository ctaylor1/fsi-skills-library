# Lifecycle interpretation

Authorization, hold, presentment, clearing, settlement, funding and posting are
separate reported events. Authorization approval does not prove a hold was placed;
only an explicit hold record establishes a recorded hold. The package sums amounts
within one transaction and currency and labels these as supplied stage amounts.
It never adds different stage totals together as a payment value.

A current participant/jurisdiction profile can declare multiple presentments and
whether presentments release holds. It cannot establish source truth. Residual holds
are computed only when amounts and links are unambiguous. Missing values stay null;
explicit zero stays zero. Explicit hold releases plus inferred presentment releases
are unresolved until allocated. Multiple holds under one authorization need allocation.
Reversed presentments do not establish hold restoration. Authorization reversal or
expiry requires explicit release evidence or a separate implemented release rule.

Duplicate event IDs or source-system/source-record pairs are quarantined across
transactions, including across currencies. Separate presentments are not duplicates
merely because their authorization is shared. Negative amounts are rejected; use
explicit reversal event kinds. Cross-currency events are quarantined, with no implied
FX. Offset timestamps are mandatory for event ordering; the analysis date does not
constitute a business-day/hold-expiry calendar. Events remain in supplied order and
retain timestamp evidence, so the analyst must explain chronological conflicts.

Source-authority mappings for clearing, settlement, funding and posting are supplied
profile claims. The script reports missing mappings and never verifies completion or
funds availability. Missing or stale profiles leave operation/hold rules unresolved.
There are no universal card hold durations, clearing deadlines or reissue rules.

Lost-card, replacement and token states require their own evidence and issuer/token
service rules. Reissue does not automatically close the underlying account or move
recurring credentials. Use `payment-credential-authentication-reviewer` for scoped
token, account-updater and authentication evidence, retaining exact credential and
payment bindings. Neither package provisions tokens or changes payment authority.
