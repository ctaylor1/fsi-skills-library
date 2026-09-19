# Design decisions and limits

The program blueprint separates proposition, legal roles, operational responsibility,
funding and customer-funds treatment. A processor role does not imply that the
processor holds customer funds, takes credit risk or is the issuer. A direct bank
issuer may also sponsor and manage its own program when this is explicit.

The deterministic responsibility rows are repository design-review criteria, not
universal legal mandates. All programs examine issuing accountability, authorization,
ledger posting, settlement, disputes, card/token servicing, fraud and customer support.
Credit adds credit-policy ownership, receivables funding and collections; debit adds
deposit account servicing and balance availability; prepaid adds customer-funds
protection and redemption. Rewards add funding/redemption responsibility.

A single supplied accountable party and cited agreement/procedure are needed per
responsibility. Duplicate assignments and unknown party IDs remain gaps. Funds flows
must identify endpoints, currency, purpose and trigger. An API call or settlement
report does not establish cash custody. Prepaid labels do not by themselves establish
e-money status, coverage, safeguarding or an exemption. Adding credit features can
change applicability; commercial use does not automatically remove all protections.

Initial US/EA/UK coverage is a structured proposition and evidence assessment, not a
complete jurisdiction-specific licensing engine. An additional territory is a
separate scoped review. Consumer obligations, issuer permissions, funds ownership,
insolvency treatment, credit features and local implementation remain visible open
questions for the regulatory and banking owners.
