# Exact supplied-data schema — 0.1.0

`evals/files/request.json` is a complete synthetic example. Required arrays must be
explicit (including empty arrays); each has at most 1,000 objects. Named IDs are
nonempty and unique within their array. ISO dates are `YYYY-MM-DD`. Optional domain
facts may be null/absent where stated, creating findings instead of invented values.
All material objects below carry `source_ids: [registry_id, ...]`; missing, duplicate
or unknown citations produce evidence findings. No unrecognized input property
contributes to a priority or financial calculation; it is retained in the snapshot.

## Envelope and scope

| Field | Contract |
| --- | --- |
| schema_version | Exactly `wealth-p0-v1`, the shared wealth envelope version. |
| request_id | Nonempty durable request ID. |
| scope_type, book_id, household_id | `advisor-book`, nonempty book ID, and exactly `book:<book_id>`. This is a collection marker. |
| as_of | Valid ISO date, the observation cutoff. |
| engagement | `{capacity: advisory\|brokerage\|private-bank\|trust, jurisdiction: US, source_ids}`. One capacity per run. |
| sources | Nonempty registry of `{source_id, reference, owner, as_of, valid_until}`; IDs unique, all text nonempty, source.as_of <= request.as_of <= valid_until. |
| currency | Exactly `USD`. |
| period_start, period_end | Dates with start <= end <= as_of. Defines cohort and economic period. |
| planning_end | Date from as_of through as_of + 366 calendar days, covered by policy validity. |
| population_complete | Boolean or null/absent. Only sourced true supports full-book totals and rates. |
| scope_source_ids | Registry citations establishing roster completeness and scope. |
| upstream_issues | Required explicit list of `{artifact_id, code, message, status: unresolved\|resolved, source_ids}`. A resolved row also requires `resolution: {owner, reference, as_of, source_ids}` with nonfuture date. Top-level unresolved_issues is rejected until explicitly mapped. |

## Policy
Required `policy` object:

- `version`, `owner`: nonempty attribution, not approval proof.
- `capacity`, `jurisdiction`: exactly match engagement.
- `effective_date <= as_of <= valid_until`; valid_until also covers planning_end.
- `source_ids`; `review_owner_id`: ID in owners or an explicit finding.
- `effort_basis`: exactly `incremental-nonoverlapping-task-minutes`.
- `evidence_gap_effort_minutes`: integer 1..100000, including integer decimal strings.
- `priority_rules`: exactly one row per trigger, each `{trigger, rank, rationale, source_ids}`.
  Trigger set: review-overdue, review-due, evidence-gap, life-event, service-request,
  retention-concern, client-requested-growth, upstream-issue. Rank is integer 1..100;
  rationale nonempty. Growth must have a strictly larger rank than every other trigger.
- `service_tiers`: nonempty unique `tier_id` rows with `label`, `review_interval_days`
  integer 1..3660, `initial_review_days` integer 0..3660, `review_effort_minutes`
  integer 1..100000, and `source_ids`.

## Owners and households
`owners`: unique `owner_id` rows with `source_ids`, `availability_complete` and
`queue_overlap_reviewed` booleans or null/absent. Both must be explicitly true for
evaluated capacity. Required `availability` array contains unique `date` rows inside
the planning window, `working_minutes` and `unrelated_committed_minutes` (integer
0..1440 or null/absent), and `source_ids`. A complete empty array means zero slots.

`households`: nonempty unique actual `household_id` rows (no `book:` prefix), with:

- `owner_id`, `tier_id`, `segment_id`: nonempty text or null/absent.
- `segmentation_basis`: service-model, documented-planning-complexity or
  relationship-stage; null/absent creates a context gap.
- `joined_on`: nonfuture date or null/absent.
- `departed_on`: REQUIRED explicit null for currently active, or nonfuture departure
  date not before known joined_on. No absent-as-active assumption.
- `review_history`: required `{status: known|none|unknown, last_completed_on, source_ids}`.
  Last completion is null/absent or a nonfuture date not before known joined_on.
  Only known status can contain a date. Known status without a date remains unknown.
- `source_ids` supporting identity, ownership, service tier, segment and relationship dates.

## Documented signals
`signals`: required list of unique `signal_id` rows. Each requires actual
`household_id`, nonempty `description`, `kind` = life-event, service-request,
retention-concern or client-requested-growth, and `source_ids`.
`observed_on` is a nonfuture date or null/absent; `due_on` is a date not before a
known observation or null/absent; `estimated_minutes` is integer 1..100000 or
null/absent. These unknowns block allocation. `client_interest_confirmed` is
boolean/null/absent; growth requires true. Other triggers do not require that flag.
Outside-book or departed-household signals remain blocked. No unsourced owner routing.

## Economics
Required `economics` object always has `source_ids` and `status`:

- `not-provided`: requires nonempty `reason`; returns null measures.
- `provided`: requires nonempty `definition_version`, period_start and period_end
  exactly matching the request, and `household_records` unique by actual household_id.
  Records must cover every supplied household overlapping the period, including departures.

Each economic row has source_ids and these amounts: `opening_assets`, `closing_assets`,
`external_inflows`, `external_outflows`, `internal_net_transfer`, `market_change`,
`fees_debited`, `recognized_revenue`, `direct_service_cost`. Values are finite JSON
numbers or decimal strings with at most 8 decimal places, from 0 to 10^15; only
internal_net_transfer and market_change allow negatives down to -10^15. Null/absent
is unknown. The schema does not infer accounting policy from an amount or fee.

## Output and commands
Every CLI accepts one input JSON path or `--selftest`. Input/output validators print
`{"errors": []}` and exit 0 for a valid object; invalid input exits 1. Calculator
prints a complete JSON artifact or an errors object with exit 1. No path is written.

The shared output contains skill, schema version, context, sources, input_hash,
artifact_id, status (`review-ready|needs-data`), findings, result and the fixed
human-review/no-action/no-delivery posture. `result` contains the complete
input_snapshot, preserved policy/upstream issues/handoff_context, book_id/scope_type,
planning_end, review_calendar, tier_coverage, cohort with member IDs, action_plan,
signals_register, owner_workloads, capacity_calendar, economics, boundaries and
draft_markdown. Unknown calculated values are JSON null; money values are cents
strings. Per-action allocations contain date/minutes; they are internal estimates.
Validation rebuilds all fields from the snapshot and rejects any output mutation.
