# Optional agent-commerce evidence contract

This is the library's normalized review contract, not a protocol message format.
Use it only for delegated agent purchase evidence. Existing core CLI schemas are
unchanged. US/EA/UK source-bound analysis is supported; other legal regimes require
an explicitly implemented module. No country label establishes legal applicability.

Use the common 1.0 envelope: request_id, as_of (ISO date), jurisdiction, participant,
requested_action analyze/draft, registered sources, upstream_issues and data.
All evidence objects listed below, including each cart item and history row, require
nonempty registered source_ids. Reference strings are opaque; do not supply payment
tokens, PANs, authentication secrets, signing keys or full signed credentials.

## Common fields

- `review_at`: timestamp with an offset. Its UTC date must equal envelope as_of.
  `proposal.execution_at` cannot precede review_at. These are supplied review
  timestamps, not a live clock or a live revocation lookup.
- `intent`: intent_id, principal_ref, agent_ref, currency, purpose; nonempty unique
  merchant_refs and item_refs; max_per_payment and total_limit; max_payments,
  delegation_depth, max_delegation_depth; allows_subdelegation and revoked; valid_from,
  valid_until. Amounts are nonnegative decimal strings; counts/depths are nonnegative
  integers. Scope must cover review and proposed execution. Revocation must be
  explicitly false; a missing/null value remains unresolved. Subdelegation must be
  expressly allowed and within the declared depth; native review does not verify a
  cryptographic delegation chain or prove a protocol supports subdelegation.
- `proposal`: instruction_id, principal_ref, agent_ref, merchant_ref,
  payee_account_ref, credential_ref, checkout_id, cart_hash, positive amount,
  currency, execution_at, merchant_origin, idempotency_key. Exact identities and
  currency must match the intent; the merchant must be allowed.
- `cart`: checkout_id, merchant_ref, currency, items, tax, shipping, discount.
  Each item has item_ref, positive integer quantity and nonnegative unit_amount.
  All money is a decimal string in cart currency. All monetary components are
  mandatory; absent charges are unknown, not zero. Items must be unique and allowed.
  The calculated total is sum(quantity × unit_amount) + tax + shipping − discount.
  It must be positive and exactly equal proposal.amount. No implicit FX or rounding
  is applied. Normalize provider precision explicitly before building this input.
- `cart_hash` is the bundled payment_contract.stable_hash of the complete cart,
  including its source references. This is a normalized-content hash, not the hash
  of an AP2 JWT, a signature, or an authenticated merchant receipt.
- `review`: intent_hash and proposal_hash computed over the complete corresponding
  objects; jurisdiction and participant matching the envelope; observed_at and
  valid_until covering review and execution; plus nonempty accountable_owner_ref,
  principal_identity_ref, agent_identity_ref, intent_review_ref,
  merchant_verification_ref, revocation_check_ref, policy_review_ref,
  human_oversight_ref and atomic_reservation_review_ref. Compare these references
  against actual external evidence before using the packet. Presence does not prove
  the review occurred or authorize execution. Refresh bindings after any scope change.
- `protocol`: family ap2/acp/institution-defined, version, source_ref,
  deployment_profile_ref, interoperability_review_ref, verification_review_ref.
  Explicit version and institution mapping are required even for a public protocol.
  The library never validates protocol conformance; see the separate protocol reference.
  AP2/ACP-claimed agent-to-agent subdelegation remains an explicit unsupported gap
  in this module. Institution-defined depth review is not protocol compatibility.

## Spend and replay history

`ledger_complete` must be explicitly true for numerical available budget.
`history` is a list of unique economic payments under this intent, not attempt logs.
Each row requires instruction_id, intent_id, idempotency_key, checkout_id, currency,
observed_at and state settled/pending/failed/unknown. Known settled/pending rows need
positive decimal-string amount; null remains unknown. A failed economic payment
needs terminal_nonexecution_ref before it can be excluded. A timeout is not failure.
Rows cannot be future-dated, cross-intent or cross-currency. Duplicate instruction,
idempotency or checkout identities are rejected; normalize attempts first.

Settled and pending spend/counts consume the intent limits. Unknown outcome, amount,
scope or incomplete history leaves both available budget and remaining count null.
Known remaining budget is total_limit minus committed spend; a negative result is
retained as a breach. Review also checks proposed amount and count against the
remaining limits. A reused instruction, idempotency key or checkout requires retry
investigation even when a prior record claims failure. This mode supports one
economic payment per checkout; split tender and multiple captures require a separate
explicit model. Refunds do not silently replenish this mandate's spending allowance.

Arithmetic is a snapshot. The helper neither creates nor verifies atomic reservations
and does not guarantee safety under simultaneous requests or cross-agent spending.
The same intent ledger must cover all relevant agents and reservations; recheck at
the separately authorized payment boundary in the deployed system.

## Mode-specific evidence

The module is selected by its installed entrypoint, never by a data field.

**Initiation mode:** common intent/cart/budget/replay review. Then assemble the core
initiation schema for exact account, rail, screening, account verification, authority
and duplicate-history checks. An agent packet is not a native bank/card instruction.

**Credential mode:** add `credential`: credential_ref, principal_ref, agent_ref,
merchant_ref, merchant_origin, currency matching proposal; state active/disabled/unknown;
single_use true, prior_use_ids empty; max_amount; valid_from/valid_until covering
review/execution; authentication_binding_hash matching the complete proposal;
authentication_review_ref, token_domain_review_ref and revocation_review_ref.
This bounded mode evaluates proposed single-use delegated credentials. It does not
release a token, verify a passkey, or determine SCA or liability shift.

**Platform mode:** add `platform`: merchant_ref, payee_account_ref, checkout_id,
cart_hash matching proposal, plus platform_ref, seller_ref, merchant_of_record_ref,
customer_disclosure_ref, terms_ref, refund_owner_ref, dispute_owner_ref, payout_owner_ref
and delegation_acceptance_review_ref. The responsible entities may differ; explain
the legal/contract model and use the platform funds-flow module for actual allocation
and payout analysis. A purchase does not establish funds receipt or seller payout.

## Execution and interpretation

Run `python scripts/validate_agent_input.py INPUT.json`,
`python scripts/review_agent_commerce.py INPUT.json`, then
`python scripts/validate_agent_output.py OUTPUT.json --input INPUT.json`.
Use `evals/files/agent-request.json` as the complete synthetic shape.

Output records exact proposal binding, calculated cart amount, available budget/count
or null, findings, sources and target-native handoffs. `supplied-evidence-for-human-review`
does not mean approval. Authority, credential release, reservation creation, payment
submission, cryptographic verification and protocol-conformance verification remain
false. Upstream issues remain gaps even if the module's local arithmetic reconciles.
