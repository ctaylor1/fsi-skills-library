# Source map — Claim File Quality Review

## Native input
Claim identity/type, as_of, config_version, policy and coverage citations, documents/events/reserves/payments/decisions. Financial evaluation requires explicit currency and financial_collections_complete:true. Reserves require balance_id, entry_type:outstanding_balance, amount, currency, as_of and source_ref. Payments require unique payment_id, entry_type:payment_transaction, nonnegative amount, currency, date and source_ref.

## Provenance
Prefer the supplied claim/plan/policy system record and the current, approved configuration for
this represented party, jurisdiction and task. The scripts read JSON only; they do not fetch,
authenticate or determine completeness of a remote system. Record top-level as_of, context and
sources as described in [insurance-contract.md](insurance-contract.md). A missing source or
configuration is a gap, not permission to invent a citation or substitute another role’s file.

## Identity and dates
Keep notification, claim, member, policy, document, transaction and revision IDs distinct.
Explicitly document cross-system/skill mappings and retain the source and target identities.
Calendar dates use YYYY-MM-DD; receipt timestamps carry an explicit timezone. No identifier,
hash, document type or supplied signature flag establishes authenticity by itself.

## Synthetic evaluation material
Files under evals/files are synthetic regression records. Their sources and version labels are
not legal authorities, production connector IDs or deployment approvals. Existing legacy input
fields are retained only where the current domain rules document their interpretation.
