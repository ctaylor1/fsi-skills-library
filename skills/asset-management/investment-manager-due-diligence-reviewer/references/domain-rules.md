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

## Investor-side diligence domain records

This first version is limited to one household and manager strategy under `wealth-p0-v1`, even
though Asset Management owns the reusable diligence job. It is not an institutional mandate,
fund legal/operational audit, return forecast, eligibility decision or manager-selection engine.
Top-level `currency` is USD. `manager` requires manager_id, name, strategy_id, strategy_name,
source_ids. Names describe the supplied record, not independently verified identities.

`policy.monitoring_interval_days` is an integer 1–366. `policy.criteria[]` contains unique
criterion_id, dimension investment/operations/fees/liquidity/evidence, description, operator,
threshold, boolean required, boolean independent_evidence_required, source_ids. Each of the
five dimensions must have at least one explicitly required criterion. Operators:
- minimum/maximum: finite numeric threshold, compare supported numeric observation.
- equals: nonempty text or boolean threshold; exact type/value comparison, no synonym inference.
- documented: threshold null; an explicit supported nonnull observation is recorded, not scored; explicit boolean false is a criterion concern rather than positive documentation.

The professional's policy supplies meaningful questions and criteria for investment process,
team, track record/benchmark and risks; custody, valuation, auditors and operational controls;
all-in fees; redemption/lockup/gate terms; and evidence ownership, recency and corroboration.
No universal thresholds, ordinal rating or weighted score is embedded.

`evidence[]` has unique evidence_id, criterion_id, value (finite number, text, boolean or null),
substantive narrative, origin manager-reported/independent/firm-record, observed_date and review_by
(exact ISO or null), source_ids. Each criterion needs one current supported observation; competing
observations remain not evaluable until the owner supplies a consolidated cited observation.
An independent-origin label does not prove independence. Numeric operator/type mismatch is a gap.
A required independent source supplied only by the manager is a gap, not corroborated evidence.

`fee_illustration` is an object or explicit null. Required fields are `method` exactly
one-period-no-high-water-mark, positive `capital`, nonnegative management_bps/other_bps,
gross_return/hurdle_return decimal rates between −1 and 10, incentive_rate fraction 0–1,
source_ids. Missing numeric inputs suppress the illustration. It is a supplied scenario, not
actual investment performance or quoted contractual fee computation.
- base_fee = capital × (management_bps + other_bps) / 10000.
- incentive_base = max(capital × (gross_return − hurdle_return) − base_fee, 0).
- incentive_fee = incentive_base × incentive_rate; total fee = base + incentive.
- illustrated net gain = capital × gross_return − total fee.
No fee tiers, timing, catch-up, high-water marks, taxes, valuation or multi-period cash flows are
modeled. Unsupported structures need an independently calculated specialist analysis, not an
invented adaptation. Decimal amounts are rounded half-up to two decimals at output only.

`liquidity` is an object or explicit null: nonnegative amount_under_review; notice_deadline,
request_date and expected_settlement_date (ISO dates or null); boolean gate_or_suspension_possible;
source_ids. These are professionally supplied scenario dates, not calculated redemption rights.
A request after its notice deadline or settlement before request is a schedule conflict.
`household_liquidity_needs[]`: unique need_id, description, needed_by current/future ISO date,
nonnegative amount or null, source_ids. An empty list means context not supplied, not no needs.

## Comparison, output and monitoring

Criteria report meets-supplied-criterion / criterion-concern / not-evaluable with full threshold,
observation and source records. Required concerns and gaps produce findings. No aggregate score
or selected manager is emitted. The full dimension-specific evidence is retained, not headings.

Compare expected settlement with each household needed-by date and cumulative amounts ordered
by date/need ID with amount under review. Any earlier unknown amount prevents a later complete
cumulative assessment. Gates/suspensions explicitly qualify all modeled liquidity; no access is
assured. Fee and liquidity results are separate illustrations, not suitability conclusions.
The monitoring plan is a dated review agenda using the supplied interval plus unresolved-item
questions; it configures no live monitoring or automatic alerts.
