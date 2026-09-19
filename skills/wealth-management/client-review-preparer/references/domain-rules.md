# Client-review request v0.2

## Request and applicability
Required top-level values: `request_id`, `author_id`, `as_of_date` (ISO), `config_version`,
`template_version`, `template_contract`, `engagement`, `disclosure_config`, explicit nonnegative
`freshness_days`, `critical_freshness_days`, and nonempty `reviews[]`.

`engagement` supplies one capacity (advisory, brokerage, private-bank, trust) and jurisdiction US.
`template_contract` records matching version, owner, approved_by and unexpired valid_until.
`disclosure_config` records matching config version/capacity, owner, approved_by, valid_until,
`required_roles` and `by_review_type` mapping annual/semiannual/ad-hoc to approved disclosure IDs.
An explicit empty list means the approved policy requires none; an absent mapping is an error.
The fixture policy is illustrative, not a legal rule or universal annual Reg BI/CRS requirement.

## Household review records
Each record has unique nonempty `client_id`, `review_id`, household_name, advisor, supported
review_type, boolean entity_resolved, accounts, sources and the material content lists.
Sources: unique source_id, system, ref, owner, date, valid_until. Require
source.date <= request.as_of_date <= source.valid_until. Any age exception (`stale_ack`) requires
`stale_ack_by` and `stale_ack_reason`; it cannot override invalid source validity.
Accounts: unique account_id, type, registration, finite reported_value, source_id.
Holdings: known account_id, security, asset_class, finite market_value, source_id.
Performance: known account/household scope, period, finite return_pct, optional finite benchmark_pct,
source_id. Other material rows are goals, plan_items, prior_notes, service_history, life_events,
open_actions, discussion_questions and disclosures; each requires its substantive label and source_id.
Open actions require owner, ISO due_date and status open/closed/cancelled. See the request fixture
and `scripts/validate_input.py` for field names; blanks must not be silently coerced to zero.

## Deterministic business states
In order: needs-data (household/advisor/accounts/goals), unresolved-entity, account-identity-gap,
unsupported-content, stale-source, tieout-break, disclosure-gap; otherwise draft-review.
Holdings sum to each reported account value to two decimals; accounts sum to household value.
No performance-return calculation is performed. The caller must provide aligned valuation/currency
conventions; this package does not normalize FX, accrued-interest, held-away or private-asset data.

Each package contains substantive review data plus a brief, discussion agenda and deck outline.
The output validator recomputes from the retained input snapshot and checks full output equality,
then applies content/identity/tie-out and prohibited-language screens. Reproducibility is not source
truth or semantic entailment. Humans check underlying evidence and deployment applicability.
