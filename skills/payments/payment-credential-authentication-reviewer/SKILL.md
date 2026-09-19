---
name: payment-credential-authentication-reviewer
description: Review network-token, wallet and stored-credential lifecycles, account-updater changes and payer-authentication evidence for a defined payment journey. Use for token provisioning, domain restrictions, 3DS/passkey design and credential operations; payment intent, legal applicability and execution remain separate controls.
license: MIT
compatibility: Python 3.10+ offline JSON evidence review; no token, identity, cryptographic-verification or payment connector bundled.
metadata:
  aws-fsi-category: "Payments"
  aws-fsi-skill-type: "Analysis and evaluation skills"
  aws-fsi-risk-tier: "R3"
  aws-fsi-archetype: "Analyze & review"
  aws-fsi-agent-pattern: "Interactive decision-support copilot"
  aws-fsi-delivery-wave: "Payments Phase 3"
  aws-fsi-action-mode: "Read-only analysis"
  aws-fsi-scheduled-agent: "no"
  aws-fsi-baseline-status: "new"
  aws-fsi-human-approval: "required"
  aws-fsi-data-classification: "Confidential; opaque credential references only"
  aws-fsi-jurisdictions: "US, euro area and UK; supplied institutional applicability review required"
  aws-fsi-owner: "Payments identity and credential controls"
  aws-fsi-primary-user: "Merchant, issuer, wallet and payment security teams"
  aws-fsi-version: "0.2.0"
  aws-fsi-recertification-date: "2027-09-18"
---

# Payment credential and authentication review

Separate the credential, its permitted domain, the authentication result, exact payer
intent and financial authorization. A network token is not interchangeable with a
merchant vault token. A passkey sign-in, 3DS result or account update cannot establish
consent for another payment or guarantee authorization, SCA compliance or liability shift.

Read [references/schema.md](references/schema.md) before extracting evidence. Keep
opaque identifiers and item-level sources; never copy PAN, token values, biometric
material, cryptographic assertions, passwords or authentication secrets. Compare the
original records with the normalized input before relying on calculated findings.

1. Identify credential kind, account linkage, token requestor/merchant/device domain,
   state, validity, provisioning controls and revocation/notification responsibilities.
2. Map each proposed use or lifecycle operation to that exact credential and scope.
   Preserve failed, unknown, suspended and deleted states. For account updater, retain
   before/after references and opt-out/consent status; an update cannot renew a mandate.
3. Inspect the actual authentication provider result, protocol/version and transaction
   binding. Keep request, challenge and final result distinct. Never infer success from
   challenge initiation or protocol use. Obtain a scoped specialist view of any claimed
   exemption or SCA applicability before customer-facing conclusions.
4. Run `python scripts/validate_input.py INPUT.json`, then
   `python scripts/calculate_or_transform.py INPUT.json`. Review every gap; a complete
   supplied declaration is still evidence for review, not authenticated proof.
5. Draft [assets/output-template.md](assets/output-template.md), then run
   `python scripts/validate_output.py OUTPUT.json --input INPUT.json`. Handoff exact
   instruction controls separately; do not provision, update, suspend, delete or pay.

Use [references/domain-rules.md](references/domain-rules.md) for trust boundaries,
[references/source-map.md](references/source-map.md) for source/version selection,
[references/controls.md](references/controls.md) for action and data limits, and
[references/handoffs.md](references/handoffs.md) for ownership.

## Phase 4 agent-commerce evidence

For delegated shopping/payment designs, use the optional credential module in
[references/agent-commerce-schema.md](references/agent-commerce-schema.md).
Read [references/agent-commerce-protocols.md](references/agent-commerce-protocols.md)
for current AP2/ACP source distinctions and deployment responsibilities. Retain
original principal consent, allowed items/merchants, exact cart/proposal binding,
revocation/expiry and complete spend/reservation history. A text prompt, successful
sign-in or protocol label cannot substitute for these records.

Run `python scripts/validate_agent_input.py INPUT.json`,
`python scripts/review_agent_commerce.py INPUT.json`, then
`python scripts/validate_agent_output.py OUTPUT.json --input INPUT.json`.
This separate schema leaves the existing CLI unchanged. Explain calculated cart
amount, remaining budget/count or unknowns, and the accountable reviewer for each
gap. Complete target-native core controls separately. No crypto verification, token
release, atomic reservation, payment submission or execution approval is implemented.
