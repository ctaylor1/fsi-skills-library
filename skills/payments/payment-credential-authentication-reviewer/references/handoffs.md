# Handoffs

- payment-initiation-control-reviewer: exact instruction, payer intent, scoped authority and credential/authentication gaps; credential possession alone is insufficient.
- payment-platform-architecture-reviewer: provider linkage, revocation propagation, event identity and idempotency requirements.
- payment-regulatory-applicability-reviewer: participant/product/jurisdiction facts and claimed SCA/exemption implications.
- card-lifecycle-operations-assistant: source-reported card/token state and operational event context; retain separate financial stages.

Use [payment-contract.md](payment-contract.md). A transport envelope is not a target
input or approval; validate the independently assembled native target request.

## Agent-commerce handoffs

Retain original scoped consent, cart/proposal hashes, revocation/expiry, full spend
and reservation history, sources and unresolved issues. Use the optional agent
modules in `payment-initiation-control-reviewer`,
`payment-credential-authentication-reviewer` and `platform-payment-flow-designer`
for their respective mandate, credential and merchant-responsibility reviews.
Then assemble the original core target schemas; the common agent packet is not a
complete payment instruction, token operation or payout authorization.
