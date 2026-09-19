# Prospect/referral schema and deterministic rules

## Shared contract
`schema_version` is `wealth-p0-v1`. Required: `request_id`, `household_id` (an explicitly
provisional prospect case ID is permitted), ISO `as_of`, `engagement` with capacity
advisory/brokerage/private-bank/trust, jurisdiction US and `source_ids`. `sources` is a nonempty
unique registry `{source_id, reference, owner, as_of, valid_until}`. Each registry entry must
satisfy `source.as_of <= request.as_of <= source.valid_until`; malformed/stale sources reject input.

`policy` requires version, owner, matching capacity/jurisdiction, current effective_date and
valid_until, source_ids. `upstream_issues` is an explicit array, empty allowed. Each row:
`{artifact_id, code, message, status: unresolved|resolved, source_ids}`. Resolved rows also require
`resolution: {owner, reference, as_of, source_ids}` with nonfuture date. These record attributed
evidence, never authenticate resolution or grant authority. Unresolved issues remain findings.

Every material object and nested row below requires `source_ids`; unknown or missing item sources
are findings. Lists are explicit, capped at 1000 rows. IDs are nonempty and unique within the
named register. Date fields accept exact ISO strings or null where unknown; current records need
both start and validity dates. Missing dates are findings, not defaults. Unsupported selections,
malformed values and duplicate identifiers reject input.

## Domain schema

`policy` adds:
- `allowed_channels`: nonempty unique subset of email/manual-phone.
- `permitted_source_kinds`: nonempty subset of firm-record/prospect-provided/referrer-provided/
  approved-public-record. Public source status never implies permission.
- `max_fact_age_days`: integer 1..3660, supplied freshness rule.
- `contact_basis`: exactly documented-affirmative-permission-only. This stricter workflow choice
  is not a universal statement of marketing law; no exception path is implemented.
- `regulatory_profile`: SEC-registered-adviser/state-registered-adviser/FINRA-member/bank-trust/
  dual-registrant. The human supplies actual applicability; no rule regime is inferred from capacity.
- `services[]`: unique service_id, name, scope, discussion_question, source_ids. These are sourced
  descriptions of professional services, not products, performance claims or client recommendations.

| Object/register | Required fields |
| --- | --- |
| prospect | prospect_id, display_name_masked, identity_basis provisional-prospect-case/documented-existing-record, source_ids |
| firm | firm_id, display_name, representative, postal_address, opt_out_instruction, source_ids |
| outreach_request | channel email/manual-phone, purpose_id exactly introductory-service-discussion, nonempty unique service_ids, source_ids |
| research_permissions[] | unique record_source_id resolving to registry, kind from policy vocabulary, status permitted/denied/unknown, owner, permission_reference, permitted_uses list from internal-research/outreach-drafting, effective_date, valid_until, source_ids |
| facts[] | unique fact_id, text, record_source_id, topic, evidence_state documented/reported, sensitivity ordinary-service-context, observed_date or null, source_ids including record_source_id |
| service_candidates[] | unique candidate_id, service_id, nonempty supporting_fact_ids, source_ids |
| channel_permissions[] | unique permission_id, prospect_id, firm_id, purpose_id, channel, status granted/denied/withdrawn/unknown, basis prospect-direct/authorized-representative/public-record/referral-only/unknown, authority_reference locator or null, effective_date, valid_until, source_ids |
| contact_controls[] | unique channel all/email/manual-phone, opt_out_status none-recorded/opted-out/unknown, screening_status recorded-no-block/block-recorded/unknown, checked_at, valid_until, source_ids |
| review_records[] | unique review_id, topic, status recorded/pending/conflicting, applicability applies/not-applicable/unresolved, rationale, owner, reference, as_of, valid_until, source_ids |

Allowed fact topics are service-interest, professional-context, engagement-preference and
existing-relationship. No protected traits or sensitive profiling is accepted. Explicit structured
keys protected_traits, race, ethnicity, religion, sexual_orientation, gender_identity,
medical_diagnosis, genetic_information and political_affiliation are rejected anywhere. This
screen does not establish that prose is free of sensitive inference; semantic review remains required.

Review topics: privacy-data-use, marketing-content and channel-permission always require one
current recorded review. Referrals also require referrer-authority and referral-compensation.
Every conflicting supplied review or unresolved applicability remains a finding, including an
extra review outside the required subset. Applicability labels/rationales are attributed reviewer
evidence, not this package's legal findings. A not-applicable record explains a determination
already attributed to its owner; it does not skip the package's permission/suppression requirements.

## Referral object
`referral` is explicitly null for no referral or an object with referral_id, referrer_id,
referrer_name_masked, relationship_description, referral_date, source_ids and
`referrer_relationship_to_firm`: client/nonclient/affiliate/unknown. Unknown relationship remains
open; the script never characterizes a testimonial or endorsement from the name alone.

Nested objects:
- `sharing_authority`: status documented/denied/unknown, prospect_id, firm_id, reference,
  record_source_ids, effective_date, valid_until, source_ids. Referrer-provided facts cannot be
  used unless this current evidence covers their source and this specific prospect/firm.
- `incentives`: status none/cash/noncash/mixed/unknown, amount (nonnegative finite number or
  decimal string up to 8 decimal places, or null), currency USD, description, source_ids.
  None requires explicit zero; compensated kinds require a positive amount/value. Unknown
  noncash valuation remains unknown; this module does not value it, calculate fees or pay anyone.
- `conflicts`: status none-recorded/identified/unknown, description, source_ids. Identified
  conflicts remain visible even if specialist review is recorded; unknown conflicts withhold draft.
- `disclosure`: version, substantive text, source_ids. Text is sourced controlled content requiring
  independent review for the actual arrangement, client/promoter status and applicable requirements.

## Assembly and output invariants
1. Use only cited, permitted, sufficiently recent facts. Exclude unsupported facts from service
   inference, preserving their IDs as not-used and the original controlled input snapshot.
2. Link each service candidate to accepted facts and sourced firm services. Output questions,
   never a fit score. Outreach use additionally requires outreach-drafting permission for every
   supporting record; internal research permission alone cannot enable a draft.
3. Require exactly one selected-channel permission with matching prospect, firm and purpose,
   current dates, granted status and prospect-direct or documented representative basis. Public
   data/referral-only never qualifies. Competing records are not resolved automatically.
4. Require explicit current global AND selected-channel controls. Opt-outs, blocks or unknown
   states suppress the draft regardless of any permission grant. No automatic opt-out expiry,
   repermission or override is inferred. Manual-phone screening is supplied evidence of the
   firm's applicable DNC/channel checks, not a live national-registry lookup or a legal conclusion.
5. Review referral sharing, economics, conflicts and applicable specialist evidence. Any finding,
   including unresolved upstream issues, withholds the complete outreach body.
6. A complete draft uses only masked greeting, sourced firm identity, controlled service scopes
   and questions, referral disclosure if applicable, opt-out instruction and postal address.
   Raw research facts, contact addresses and inferred personal claims are never inserted.
7. All output content is reconstructed exactly from the snapshot. Artifact hash is lineage, not
   authentication. Every result remains human-review-required, action_taken false and not-delivered.

`review-ready` means complete supplied evidence for internal review, not permission to communicate.
An active opt-out produces a truthful `needs-data`/withheld artifact; it is not a request to override
the opt-out. No final legal classification, consent authenticity, supervision approval or system
change is performed. Record owners must recheck controls at actual time of any separate human use.
