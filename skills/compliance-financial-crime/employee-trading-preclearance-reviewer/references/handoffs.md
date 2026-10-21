# Handoffs and ownership

`conflicts-of-interest-reviewer` owns conflict analysis. `market-surveillance-alert-investigator` owns suspected market abuse evidence. `investment-mandate-reviewer` owns firm/fund portfolio orders. Holding summaries, investment advice, account-opening consent and ongoing employee-reporting controls are separate jobs.

The upstream producer must validate its native result against the separately retained original input.
A receiving workflow must validate its own schema and retain provenance, unresolved questions,
legal scope, purpose, confidentiality and accountable owner. An ID/hash alone is not proof of truth,
completeness, an approval or recipient entitlement. Transfer only the minimum evidence needed.

No live preclearance integration, authenticated approval broker, system-of-record write, clearance issuance, notification, idempotent execution or rollback is implemented. Operational execution remains out of scope even with a supplied token. This does not place or execute trades.
