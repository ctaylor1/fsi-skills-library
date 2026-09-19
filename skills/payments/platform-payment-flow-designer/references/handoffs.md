# Handoff boundaries

- `payment-regulatory-applicability-reviewer`: receives the specific source records, findings, assumptions and exact native inputs described by the local output.
- `payment-initiation-control-reviewer`: receives the specific source records, findings, assumptions and exact native inputs described by the local output.
- `merchant-onboarding-risk-reviewer`: receives the specific source records, findings, assumptions and exact native inputs described by the local output.

Retain durable request_id/case_id, source references, versioned evidence, original exact monetary identities and unresolved issues. The bundled contract creates a draft-only transport envelope with target_validation required. It may carry an empty target_input until the caller maps the required native fields; transport validity does not establish recipient readiness. Never erase gaps or promote a design result into authority. When uncertain which workflow owns the question, return to `payments-router` with role, objective, jurisdiction and source coverage.

## Agent-commerce handoffs

Retain original scoped consent, cart/proposal hashes, revocation/expiry, full spend
and reservation history, sources and unresolved issues. Use the optional agent
modules in `payment-initiation-control-reviewer`,
`payment-credential-authentication-reviewer` and `platform-payment-flow-designer`
for their respective mandate, credential and merchant-responsibility reviews.
Then assemble the original core target schemas; the common agent packet is not a
complete payment instruction, token operation or payout authorization.
