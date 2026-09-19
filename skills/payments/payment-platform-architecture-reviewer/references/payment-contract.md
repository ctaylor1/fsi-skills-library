# Payments contract v1.0.0

This contract describes portable analysis and drafting. It supplies no production
connections, policy authority, approval credentials or permission to move money.

## Identity and lifecycle

Preserve order, payment, instruction, attempt, authorization, capture, message, case,
batch, payout and ledger-entry identifiers separately. Retain source-system identity
and one-to-many relationships. An identifier collision is an issue, not a match.
Keep participant role, legal entity and account ownership explicit.

Distinguish authentication, authorization, capture, clearing, settlement, merchant
funding and ledger posting. Approval is not settlement. A generic status code has
no universal meaning without rail, message family, participant and profile version.
Request-for-payment does not establish payer consent or completed payment.
Final settlement cannot be edited or guaranteed to roll back; a refund/return may
be a new linked instruction and a recall may only request recovery.

## Money and time

Use Decimal/minor units and an explicit currency. Missing is unknown, never zero.
Partition evidence by entity, account and currency, then by transaction or cycle
as appropriate. Do not add unlike currencies; FX conversion requires a supplied
rate, timestamp, direction and purpose. Quarantine ambiguous duplicates and
unallocated many-to-many relationships rather than selecting the first row.
Disclosed input-scope assertions are not independently verified account identity.

Keep offset-aware event timestamps distinct from local business dates, settlement
cycles and rule deadlines. Use a named calendar/cutoff profile for business-day
arithmetic. Never substitute calendar days for business days or one scheme clock
for consumer-protection obligations. Unknown finality, deadlines and authority
remain unresolved. Future-effective, draft and superseded rules are not active.

## Evidence and rules

Evidence states: supplied, retrieved, authenticated, inspected, corroborated,
sufficient, unresolved. These describe different claims, not an automatic ladder.
A reference, boolean attestation, signature flag or hash does not authenticate a
source. Reviewed claims need actor, method, time, scope and result evidence;
offline validation checks the declaration, not the reviewer's actual identity.
Evidence sufficiency also depends on period, sample, applicability and conflicts.

A rule profile carries profile_id, version, source_ref, authority, participants,
jurisdictions, status, effective_from, optional effective_to, review_due and
review_owner. Licensed scheme/provider rules stay in authorized distribution.
Public orientation references are not complete operating rulebooks. Firm policy
cannot override applicable law or network obligations. Preserve conflicts for
the responsible specialist instead of silently picking the convenient rule.

## Handoffs

A structured handoff carries contract_version, handoff_id, source_skill,
target_skill, case_id, lead_owner, requested_output, source_refs, unresolved_issues,
target_input, action_mode (read-only/draft-only), target_validation=required and
authority_granted=false. Validate the envelope and then the target's native input.
Keep original evidence and unresolved issues; do not promote upstream confidence.
The lead owns the case until an explicit handoff is accepted. A generated case ID
does not prove a case was persisted. A lineage hash is not authentication.

## Repair and servicing plans

Bind the complete input snapshot, exact before/after or linked instruction,
amount/currency, original payment, policy version, applicable fields, identity,
screening evidence, authority requirements and uncertainty to the plan digest.
Repair requires an established defect; routine refunds/returns require their own
eligibility and authority. Do not use a repair approval to authorize a return.
Execution, approval verification and idempotency enforcement belong to an
independently implemented runtime. These packages do not claim those capabilities.

## Deployment and maintenance

Canonical resources live under shared/payments and selected copies are bundled
locally for portable packages. tools/sync_payment_contract.py --check detects
drift. Behavioral evaluation, professional acceptance and deployment acceptance
are separate from schema, arithmetic and unit tests.
