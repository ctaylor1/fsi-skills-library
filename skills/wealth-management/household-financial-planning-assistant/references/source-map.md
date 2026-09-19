# Source and input contract

The scripts accept only the shared `wealth-p0-v1` envelope:

| Field | Required value |
| --- | --- |
| `schema_version` | `wealth-p0-v1` (the common contract remains version 1 in P1) |
| `request_id`, `household_id` | Nonempty internal, de-identified strings |
| `as_of` | Exact `YYYY-MM-DD` |
| `engagement` | `{capacity: advisory|brokerage|private-bank|trust, jurisdiction: US}`; select the capacity for this task |
| `sources` | Nonempty array of `{source_id, reference, owner, as_of, valid_until}` with unique IDs |
| `upstream_issues` | Required explicit list of received handoff issues; `[]` only after reviewing all received handoffs |
| `currency` | `USD`; no conversion or mixed-currency calculation |

Each source must satisfy `source.as_of <= request.as_of <= source.valid_until`. Use immutable,
version-identifying references (for example a statement snapshot ID, profile version or model
version). Each material domain object and list row requires nonempty unique `source_ids`
resolving to this registry. Scalar facts inherit their containing object's source IDs. Explicit
assumption/template versions are required below. Sources and versions are supplied evidence
metadata: the scripts do not authenticate a source, policy approval, professional capacity or
access permission. Contradictory sources require human resolution.

Wrong types, duplicates, invalid ranges, non-finite numbers, booleans used as numbers and stale
registry sources are structural errors. Absent material fields and unresolved item-level sources
produce `needs-data`. Amounts are finite nonnegative USD values in whole cents, at most 1e12;
percentages use the units stated below. Lists described as required must be present; an allowed
empty list explicitly means none, while a missing list means unknown. Do not encode missing
facts as zero, empty strings or invented defaults.

The CLI validator returns exit 0 when structure is valid, even if findings remain. Always read
findings and output status. Exit 0 is not financial readiness or professional approval.

## Upstream issue inventory

`upstream_issues` is required at the top level in both integrated and focused modes. Each row is
`{artifact_id, code, message, status: unresolved|resolved, source_ids}`. Preserve the originating
artifact, original concern, source IDs and supplied status; do not reclassify or suppress a concern
to obtain review-ready. Missing inventory/status/source evidence remains a finding. Unresolved
rows create `upstream-unresolved` findings with origin metadata; complete independent calculations
remain conditional evidence and do not clear ownership, authority or other upstream conflicts.

A row marked resolved additionally requires `resolution: {owner, reference, as_of, source_ids}`
from the responsible external reviewer. The dated, cited resolution must not postdate the request.
This records supplied resolution evidence; it does not authenticate it or constitute this skill's
adjudication. A bare resolved label cannot clear a finding. The complete inventory is carried in
`result.upstream_issues` and the full input snapshot, and is covered by output reconstruction.

## Domain schema

- `mode`: `household_plan` or `goal_progress`.
- `assumptions`: `{version, return_convention, nominal_annual_return, annual_inflation, extension_limit_months, at_risk_ratio, source_ids}`. Convention is exactly `nominal-rate-monthly-net-of-fees-and-modeled-tax`. Return is nominal annual decimal [-0.99,1], divided by 12; inflation is effective annual decimal [-0.5,1]. Extension limit is integer 1..1200; at-risk ratio 0..1. No defaults.
- `asset_pools`: nonempty rows `{pool_id, account_ids, balance, reserved_amount, source_ids}`. Account IDs nonempty unique strings, unique across pools. Reserved balance is not available for goal assignment. Pools use balances as of the envelope date.
- `goals`: nonempty rows `{goal_id, label, priority, target_amount, target_date, target_basis, monthly_contribution, allocations, source_ids}`. IDs unique, priority supplied integer 1..100 (smaller means higher human-assigned priority). Target positive, date current/future and at most 1200 whole months away; basis `nominal` or `as_of_real`. Contributions occur at month end. `allocations` may be explicitly empty; each row is `{pool_id, amount, source_ids}`, with at most one entry per pool per goal. Goal initial balance is their sum, never a separate duplicated figure.
- In `household_plan`, `cash_flow` is `{expense_basis, income, expenses, monthly_reserve_contribution, source_ids}`. Basis exactly `excludes-debt-goals-reserve;income-after-tax`. Income/expense arrays may be explicitly empty; rows `{item_id, label, monthly_amount, source_ids}`, unique IDs within each array. Enter recurring monthly equivalents from documented evidence; do not convert uncertain income silently.
- In `household_plan`, `debts` is an explicitly present array (empty allowed) of `{debt_id, label, balance, apr, minimum_monthly_payment, additional_monthly_payment, source_ids}`. APR is nominal annual decimal 0..1. These are supplied scheduled amounts, not a product recommendation. Amounts with zero balance contribute zero debt service. Debt interest accrues monthly; the final payment is capped at balance plus that month's rounded interest.
- `goal_progress` deliberately does not assess `cash_flow` or `debts`; omit them. It still checks goal pool over-allocation. Household affordability is labeled unassessed.

Output envelope is followed by a full `input_snapshot` and `result` with assumptions, cash-flow
reconciliation, debt analysis, funding ledger, goal progress, planning discussion boundary and
limitations. Amounts and IDs can be traced through snapshot and `source_ids`. `extension_months:
null` means no solution found inside the declared search limit; it is not proof that no solution
exists. A present-date target has no contribution-period lever (`null`). All projection bands are
conditional on the supplied funding schedule; they do not prove that schedule is affordable.

### Missing priority and identity evidence

A required domain field may be unknown. Supply `priority: null` when the source
has no human-assigned rank; list order is not ranking evidence. Supply
`account_ids: null` for an asset pool with unknown account membership. These
values yield missing-evidence findings rather than permission to invent facts.
Keep independently supported amounts and conflicts visible in the draft while
marking any tool calculation withheld because of those gaps. See the
source-to-input check in SKILL.md.
