# Source map — Claim Intake Preparation

## Native input
`raw_fnol{fnol_id,policy_number,loss_date,reported_date,claimant_name,loss_type_raw,cause_raw,loss_location_raw,receipt{received_at,source_ref}}`; `config{loss_type_map,cause_map,required_fields,config_version}`. Optional `claim_package` is the former readiness input with claim_id, fnol_id, identity_mapping.source_ref, policy_number, claim_type, as_of, config_version, dates, fields, documents, deadlines and explicit config.requirements.

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
