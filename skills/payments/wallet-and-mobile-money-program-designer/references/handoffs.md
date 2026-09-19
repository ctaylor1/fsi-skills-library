# Native handoffs

- `payment-regulatory-applicability-reviewer`: actual country, issuer/custody model, provider contracts, relevant funds and source dates. Map to its native schema; unsupported Kenya legal analysis remains a specialist gap.
- `payment-credential-authentication-reviewer`: opaque credentials, usage scope, authentication and exact consent/intent.
- `payment-initiation-control-reviewer`: exact proposed redemption instruction, beneficiary, amount/currency, funded capacity and authority evidence. Kenya initiation remains unsupported unless a separate native profile is supplied.

Every transport envelope retains case, sources, owner and unresolved issues; target validation remains required. Empty target_input is not a ready or authorized request. Return to `payments-router` if responsibility is unclear.
