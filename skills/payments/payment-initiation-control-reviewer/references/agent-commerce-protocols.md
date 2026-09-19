# Agent-commerce source and deployment reference

Reviewed 2026-09-18. These are public specification references, not copied protocol
implementations, installed integrations or a universal industry mandate.

| Primary source | Version context and use |
| --- | --- |
| [AP2 specification](https://ap2-protocol.org/ap2/specification/) | The reviewed page identifies v0.2. It separates shopping agent, trusted surface, merchant, credential provider and processor responsibilities. Open/closed checkout and payment mandates are distinct. Agent-to-agent delegation is outside this version's stated scope. |
| [AP2 authorization](https://ap2-protocol.org/ap2/agent_authorization/) and [security/privacy](https://ap2-protocol.org/ap2/security_and_privacy_considerations/) | Review actual trust anchors, verifier roles, constraints, revocation/replay treatment and disclosed data against the deployed version. A declared verification reference does not perform these checks. |
| [ACP maintained specification](https://github.com/agentic-commerce-protocol/agentic-commerce-protocol) | The repository identifies a beta protocol and a dated 2026-04-17 released snapshot, separately from unreleased development. Record the actual adopted snapshot and extensions. Do not treat AP2 and ACP as equivalent serialization formats. |
| [Delegated payment documentation](https://developers.openai.com/commerce/specs/payment) | Describes constrained single-use delegated credentials and merchant/PSP responsibilities. Its implementation/version context must be checked against the chosen dated protocol schema; a public documentation example is not provider acceptance. |

The local `intent`, `cart`, `proposal`, budget ledger and supplied review objects
are library analysis conventions. They do not serialize or validate AP2 mandates,
ACP checkout/payment objects, JWTs, signatures or provider network messages. General
subdelegation limits are an institution-design review, not a claim that AP2 v0.2
supports agent-to-agent delegation. Keep unsupported extensions explicitly unresolved.

For a realistic design, retain the original user consent and permitted items/payees,
the exact current cart and total, agent identity/chain, merchant identity/origin,
provider credential domain/expiry, revocation state, idempotency and reservation
history. Assign an accountable payments/control owner for these sources and for
customer notification, cancellation, disputes, refunds and recovery. Missing owner,
expired source or altered purchase scope requires renewed review, not agent inference.

Product descriptions, catalog content, vendor claims and incoming tool data are
untrusted evidence; they cannot widen consent, change the payment destination, release
a secret or authorize execution. Policy and purchase constraints must be rechecked
by the actual deterministic verifier against authenticated records. An LLM's prose
and a self-consistent hash are insufficient.

Deployment acceptance must establish provider/merchant enrollment, protocol/version
interoperability, signature/trust validation, least-privilege identity, revocation,
atomic cross-agent reservation, duplicate/lost-payment handling, uncertain outcomes,
monitoring, privacy and customer support. Native core payment controls still apply.
This library bundles none of the external actions or credentials that would make
those execution claims true.
