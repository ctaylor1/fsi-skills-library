# Relationship/account readiness rules

This package compares supplied evidence with an explicit firm policy; it does not infer legal
obligations or verify identities. `review-ready` means every configured evidence item is
present and internally consistent for human review. It never means approved, compliant or
permitted to open. `needs-data` preserves all gaps and source conflicts.

## Required policy scope
`policy` includes version, owner, source_ids, capacity and jurisdiction matching engagement.
`account_requirements` maps each supported registration to a nonempty required document-kind
list. Supported identifiers are individual, joint, ira, entity and trust; additional registration
work requires reviewed schema/policy extension. The list is a routing vocabulary, not a claim
that a single checklist covers all accounts of that type.
`consent_requirements` is an explicit nonempty list of firm-defined consent scopes.
`external_review_requirements` must explicitly address kyc, sanctions and beneficial-ownership;
each entry has boolean required plus rationale under the sourced policy. Required false is an
attributed firm-policy declaration, not this skill's legal finding. No universal RIA AML
requirement is embedded. Consult current law, firm capacity and custodian responsibilities.

## Completeness logic
1. Relationship identifier, service scope and received engagement evidence are recorded.
2. Every proposed account has registration, owner and authorized-person IDs resolving to
   supplied party records, and received authority-record evidence.
3. Every party has a role and received identity-record evidence; received is not verified.
4. Every account's policy-required document kind has received/current evidence. A conflicting,
   missing, expired or undated required document remains a gap even when another copy exists.
5. Each owner and authorized person has recorded evidence for every configured consent scope;
   declined, conflicting and pending consent remain gaps, never inferred consent.
6. Each required specialist review has completed-by-owner status, explicit no-unresolved-issues-recorded outcome, an owner reference, source
   coverage and matching owner IDs for that account. An absent/malformed applicability declaration is a policy gap but never suppresses checks for
   other explicitly required reviews. Missing, pending or escalated outcomes
   are routed to the authorized owner, never adjudicated here.
7. Every material record cites known dated sources. Unknown relationships, sources and scope
   mismatches prevent review-ready. IDs are unique within each register.

Malformed envelopes/record structures stop computation; incomplete domain facts produce a gap
list. Up to 1000 records per register. The structured output is rebuilt from its snapshot during
validation; unrecognized narrative/action additions are not part of the validated contract.

## Limitations
Institutional policy truth, legal applicability, identity authenticity, signatures, entitlements,
screening quality and regulatory approval cannot be established from supplied JSON. No account,
CRM, screening or transfer API is connected. Individual-account demo policy is not a production
standard. Complex entities/trusts require specialist reviewed evidence and checklists before use.
