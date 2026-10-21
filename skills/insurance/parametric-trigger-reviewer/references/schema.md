# Native input schema

All fields below are required unless explicitly conditional. Input is a JSON object.
Unknown evidence is null; malformed shapes fail validation. No unknown becomes zero.
Use exact decimal strings for fractional values; integer JSON numbers are allowed.
Arithmetic uses 256 significant digits and exponents bounded at +/-1000; any
operation requiring rounding or exceeding these bounds fails validation.

## Envelope and profile

`case_id`: stable text; `as_of`: YYYY-MM-DD. `context` contains capacity,
represented_party, object_id, jurisdiction and line_of_business. Use capacity
`parametric-claims-review`, line `pc`, and object_id exactly `contract_id/event_id`. `sources` is an
array of unique {source_ref, version, as_of, optional locator}; each date is known
and no later than review. `unresolved_issues` is an explicit string array.
`data` contains owner, market, program, product and **profile nested at data.profile**.
The profile has profile_id, version, reviewed_by, source_refs, jurisdictions,
lines_of_business, effective_from/effective_to, method exactly
`supplied-parametric-event-tiers-v1`, markets/programs/products arrays including the
actual scope, rule_basis and limitations. See [scope profile](specialist-profile.md).
Every contract/event/status/reading/ledger/tier record includes nonempty source_refs
resolving supplied source IDs; documentary flags need actual source statements.

`data.inventory` is a source-bound object with nonempty source_refs, locator,
reading_statement and ledger_statement. These are explicit custodian attestations
of complete reading/revision and reconciled aggregate-paid inventories, not agent
inferences. Its contract_id, event_id and aggregate_period_id must exactly match
the supplied contract/event/period. Bare completeness booleans do not suffice.

## Contract and event

`data.contract`:

| Field | Type and meaning |
| --- | --- |
| contract_id, version, reviewed_by | Known contract/version/review identity |
| effective_from, effective_to | Inclusive calendar dates covering event date |
| coverage_start_at, coverage_end_at | ISO timestamps with timezone; [start,end) |
| parameter, unit, location | Exact contract metric, unit and station/zone identifier |
| primary_verifier | Designated primary verifier identity |
| fallback_verifiers | Explicit list of other designated verifier IDs; no implied priority |
| currency | Actual contract currency; no conversion |
| aggregation | Exactly single-certified-value |
| trigger_terms_reviewed | Explicit boolean true from source review, or null/false gap |
| operator | Exactly >=, >, <= or < |
| event_cap, aggregate_limit | Known nonnegative amounts |
| aggregate_period_id, aggregate_period_start, aggregate_period_end | Named aggregate period and inclusive dates containing the event |
| basis_risk_note | Contract/exposure-specific explanation for human review |
| tiers | Nonempty array of {tier_id, threshold, payout, source_refs} |

Tier IDs are unique. Thresholds are signed exact values, strictly increasing for
>= or >, strictly decreasing for <= or <. Payouts are nonnegative and nondecreasing
in the listed severity order. No interpolation or mixing operators.

`data.event`: event_id, parameter, unit, location, occurred_at, window_start_at,
window_end_at, source_refs. Timestamps include timezone, are observed by as_of,
and occurrence lies in [window_start,window_end). The entire window lies inside
coverage. Event parameter/unit/location must match the contract exactly.

## Verifier readings and finality

`data.verifier_status`: nonempty unique verifier_id records, each with event_id,
available (explicit boolean), observed_at (zoned timestamp at or after window completion), source_refs.
`data.readings`: nonempty unique reading_id records, each with event_id, verifier_id,
revision (nonempty text version label; normalize source numeric revision IDs to exact text), supersedes_reading_id (explicit predecessor ID or null for original),
finality (final/preliminary/retracted), parameter, unit, location, window_start_at,
window_end_at, value (signed exact number), issued_at, source_refs.

Every reading binds the actual event scope and identical window instants, and must
be published no earlier than window completion and no later than review. A revision
preserves verifier and strictly advances publication time; dangling, branching and
cyclic chains are unresolved. `data.selected_reading_id` must be the only terminal
reading of the selected verifier, and it must be final. Two unrelated terminal
finals are a conflict even if their values match. A later preliminary/retraction
cannot silently leave an earlier final usable.

`data.reading_inventory_complete`: explicit boolean. Selected verifier must have
available=true for this event. A fallback must appear in the contract, with explicit
primary available=false and no contrary terminal final primary reading. No automatic
fallback, alternate station, unit conversion or latest-timestamp selection occurs.

## Paid ledger

`data.aggregate_ledger_complete`: explicit boolean. `data.aggregate_ledger`: explicit
array, empty only when affirmatively complete; unique entry_id rows contain event_id,
contract_id, currency, aggregate_period_id (exact contract period), paid_through (known calendar date <=as_of and within that aggregate period), cumulative_net_paid
(nonnegative) and source_refs. Exactly one source-reconciled net-paid record per event
is allowed; multiple payment transactions must be reconciled upstream, never added
as duplicate cumulative snapshots. A current-event payment is included in both
aggregate consumption and that event's previously paid amount with separate roles.
Its paid-through date cannot precede the event date.

## Output

The standard workflow result preserves source_document, context, findings,
unresolved_issues and artifact; arbitrary narrative is a separate draft. Native
results expose index_value, matched_tier_id (null when below every tier OR unevaluable;
use status/findings to distinguish), gross_event_scenario, current_event_recorded_paid,
aggregate_remaining and provisional_unpaid_scenario. Monetary results are Decimal
strings or null, never assumed rounding to cents. All outputs require human review
and have no approval, execution or payment authority. Source authentication and
physical-loss estimates are explicitly not performed.
