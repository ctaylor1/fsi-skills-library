# Handoffs

A handoff carries the durable request ID, jurisdiction/participant, exact source-bound result and registered evidence, all findings/upstream unresolved issues, expected next artifact and current action boundary. The receiving skill must pass its own input validator. Review-ready analysis is never an authorization token.

Initiation → `payment-platform-architecture-reviewer` for implementing runtime binding/idempotency; normal servicing → `payment-servicing-planner`; established defects → `bank-payment-exception-investigator` before `payment-repair-planner`. Financial-crime evidence gaps go to the designated human control owner, with no sanctions decision here.

## Agent-commerce handoffs

Retain original scoped consent, cart/proposal hashes, revocation/expiry, full spend
and reservation history, sources and unresolved issues. Use the optional agent
modules in `payment-initiation-control-reviewer`,
`payment-credential-authentication-reviewer` and `platform-payment-flow-designer`
for their respective mandate, credential and merchant-responsibility reviews.
Then assemble the original core target schemas; the common agent packet is not a
complete payment instruction, token operation or payout authorization.
