# Domain rules and input schema

## Common required contract
The top-level `schema_version` is `wealth-p0-v1`; supply `request_id`, `household_id`, exact ISO
`as_of`, `engagement` with `capacity` (advisory, brokerage, private-bank or trust), US
`jurisdiction`, and item-level `source_ids`. `sources` is a nonempty register of unique
`{source_id, reference, owner, as_of, valid_until}`. Every registry source must satisfy
`source.as_of <= request.as_of <= source.valid_until`; stale/future evidence rejects input.

`policy` requires nonempty `version`, `owner`, matching `capacity`/`jurisdiction`, current
`effective_date`/`valid_until`, `source_ids`, and the domain configuration below. Policy
version/owner/date fields describe supplied records; they do not authenticate institutional approval.
`upstream_issues` is an explicit array (empty is permitted) of
`{artifact_id, code, message, status: unresolved|resolved, source_ids}`. Unresolved issues
propagate into findings; resolution claims remain attributed supplied evidence.

Each material object below requires `source_ids`, including nested assumptions, conditions,
beneficiaries, resources, observations and criterion definitions. Unknown or missing item sources
produce `needs-data`. Numeric unknowns remain null; no conversion of blanks into zero.
Registers are arrays of at most 1000 objects, IDs unique within each register. IDs are opaque,
not account numbers. Text identifiers must be nonempty. Numeric values must be finite and
booleans do not count as numbers. Currency-supported workflows accept USD only; no FX defaults.

The snapshot/hash binds the supplied JSON, not the underlying source truth. Output validation
rebuilds the entire domain result and compares all content, identities, arithmetic and findings,
in addition to checking the canonical envelope. A self-consistent replacement snapshot could
still be false: compare it with approved source systems during human review.

## Estate domain records

`policy.required_document_kinds` is an explicit unique list from `will`, `trust`,
`power-of-attorney`, `healthcare-directive`, `other`. `required_beneficiary_tiers` explicitly
lists `primary` and/or `contingent`. Empty lists mean no requirement in this supplied scope,
not a legal conclusion that a document or tier is unnecessary.

- `parties[]`: unique `party_id`, masked `display_name`, `role`, `source_ids`.
- `documents[]`: unique `document_id`, `kind` above, nonempty `version` and factual `summary`,
  `status` current/superseded/unknown, historical `executed_date` or null, `source_ids`.
- `assets[]`: unique `asset_id`, `description`, `registration` individual/joint/trust/retirement/
  insurance/other, explicit `owner_party_ids[]`, explicit `document_ids[]`,
  `designation_status` documented/none-recorded/unknown, `source_ids`.
- `intentions[]`: unique `intention_id`, `asset_id`, `description`,
  `target_owner_party_ids` (unique list or null), `governing_document_ids` (unique list or null),
  `beneficiaries` (list below or null), `source_ids`. Exactly one consolidated intention per asset
  is needed for comparison. Null means not collected; an empty list is an explicit intended none.
- `designations[]`: unique `designation_id`, `asset_id`, status current/superseded/unknown,
  `document_ids[]`, `beneficiaries[]`, `source_ids`.
- Beneficiary objects: `party_id`, `tier` primary/contingent, numeric `share` fraction 0–1 or
  null, `source_ids`. No duplicate party within a tier. Each nonempty tier must total exactly
  one. No normalization, per-stirpes interpretation or legal eligibility inference occurs.

## Comparison and output

Validate cross-references and required current document kinds. A record of current status is
not proof of execution or validity. Compare intended owner-ID sets with supplied recorded owners;
compare intended document-ID sets with asset document links; compare intended beneficiary
party/tier/share schedules with a unique current designation. Multiple current or unknown-status
designations remain unresolved; superseded records are retained in the snapshot, never chosen.
Differences are literal coordination questions, not a finding of improper registration.
An account's possible non-probate treatment does not establish document precedence here.

The output's `asset_comparisons` preserves substantive asset, intention and designation records,
`literal_differences`, questions and `legal_effect: not-determined`. `documents`, `parties`,
`review_summary` and `specialist_questions` preserve scope and open items. Missing sources,
allocation problems, missing links/documents and literal differences produce `needs-data`.
A no-difference output describes only the supplied records and does not approve an estate plan.
