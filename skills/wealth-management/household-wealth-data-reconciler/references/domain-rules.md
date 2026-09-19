# Contract and calculation rules

## Common envelope
`schema_version: wealth-p0-v1`, nonempty `request_id`, `household_id`, exact ISO `as_of`, `engagement: {capacity, jurisdiction}` (one of advisory/brokerage/private-bank/trust; US only), and nonempty `sources`. Each source has unique `source_id`, `reference`, `owner`, `as_of`, `valid_until`; request date must be within source dates. Stale or malformed registry metadata is rejected, never silently accepted.

## Domain input
See the complete synthetic [fixture](../evals/files/household_example.json).
- `base_currency`: USD; no currency conversion.
- `household_party_ids`: distinct pseudonymous IDs confirmed for this household.
- `expected_accounts`: nonempty rows `{account_id, kind: asset|liability, source_ids}`. This explicit inventory defines completeness, not the records received.
- `valuation_policy`: `{version, max_age_days: integer 0..366, source_ids}`. The deployment supplies a reviewed freshness policy; seven days in the fixture is illustrative.
- `records`: list of account-level snapshots. Each has `record_id`, `account_id`, `kind`, `value`, `household_share`, `currency`, `valuation_date`, `owner_party_ids`, `identity_verified`, `is_held_away`, `source_ids`. Use null for unknown value/share/verification/held-away status; empty owner list means unknown. Account/record IDs and kind are structural requirements.
- `value`: nonnegative decimal string or integer, up to two decimals and 1e15. A liability is positive and subtracted by its kind. Floats, booleans, NaN and Infinity are rejected.
- `household_share`: explicitly sourced fraction 0..1, up to six decimals. Do not infer shares from owner count or joint registration. External co-owners are allowed when at least one household party is present and the supplied household share is confirmed with the sources.
- Optional `reference_totals`: `{assets, liabilities, currency: USD, basis: household-share, source_ids}` from an independently supplied report covering the same declared scope. No reference means `not-performed`, not a match.

## Reconciliation
Group only on supplied confirmed account ID. Identical economic snapshots consolidate records and citations; conflicting values, dates, owners, shares, kinds or held-away status exclude the entire account. Missing snapshots, unresolved mapping/ownership/share, missing or stale valuation dates, unknown sources, unsupported currency and out-of-scope accounts become findings. Never choose a winner or silently discard a conflict.

Compute each included household value = account value × share, rounded half-even to cents, then sum assets and liabilities separately. Net worth = included assets minus included liabilities. Missing/excluded accounts make these **partial** totals; zero partial totals do not mean a household owns nothing. A complete scope with unmatched independent reference still has needs-data status. Source dates alone cannot validate an asset's actual valuation.

## Output
Common evidence envelope plus `result.input_snapshot`, `included_accounts` (record/source lineage), `excluded_accounts` (reasons), `coverage`, `totals`, and `reference_tie_out`. `artifact_id` binds the full normalized input; it is not a signature or approval. Output validation reconstructs the entire artifact and independently verifies conservation arithmetic. It detects internal edits, not an attacker who rewrites the input and output consistently.
