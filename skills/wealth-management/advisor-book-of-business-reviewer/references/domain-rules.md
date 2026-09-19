# Domain rules — version 0.1.0

## One book and one capacity
The book roster includes every relationship present at the opening of the measurement
period, every joiner and departure during that period, and all relationships through
the as-of date. `population_complete: true` is an attributed scope assertion requiring
`scope_source_ids`, not an independent discovery claim. With incomplete coverage,
show received counts and known economic subtotals; withhold full-book rates/totals.

The collection envelope is `book:<book_id>`. Actual household IDs remain in all
household, signal and economic rows. `book:` is reserved and prohibited there.
One engagement capacity and USD apply to the run. Other currencies and jurisdictions
require a separate approved implementation. Capacity cannot be pooled across runs
without checking duplicate owners, clients, commitments and work.

## Service calendar and segmentation
Service tiers come from the current sourced policy. Their review cadence, first-review
interval and effort are inputs; the skill supplies no legal/default annual cadence.
`known` review history uses last completion plus tier review interval. An explicitly
documented `none` uses relationship start plus the first-review interval. `unknown`
or uncited history yields an evidence-collection task, never the first-review default.
All intervals are calendar days. Dates equal to as-of are due today; only earlier
dates are overdue. Departed relationships remain in the audit and period population
but receive no routine current-book review task.

Tier coverage fraction = active households with known, nonoverdue cadence / active
households. Publish only when population completeness is sourced and every active
household in that tier has known cadence; otherwise null. This is a policy-cadence
indicator, not a legal-compliance score or a completed-work rate. New reviews not yet
due can be within cadence. A zero-household denominator yields null.

Segments are supplied labels with a stated service-model, documented-planning-complexity
or relationship-stage basis. They organize the calendar but do not supply an opaque
priority score. Do not manufacture segments from wealth, age or protected traits.

## Priorities and client needs
Policy explicitly ranks every supported trigger and explains each rank. Smaller ranks
come first, then due date, actual household ID and action ID. Missing due dates sort
first within a rank but remain blocked, not urgent by factual inference. Growth ranks
must be strictly later than every service, retention and evidence trigger. Economics
and unrecognized attributes cannot affect this order.

Signals are documented life events, service requests, retention concerns or confirmed
client-requested growth discussions. A retention concern is an attributed observation,
not a churn prediction. Growth requires explicit sourced client interest; otherwise it
is retained as a blocked finding. No product or transfer recommendation is inferred.
Future signals remain in the register even when outside the planning window.

## Workload and daily allocation
Only a sourced owner with explicit complete availability and reviewed queue/commitment
overlap can receive draft work allocations. Policy `effort_basis` attests that task
estimates are incremental and nonoverlapping. If tasks overlap, consolidate the
estimates upstream before use; the program cannot determine meeting agenda overlap.
Subtract unrelated commitments from working minutes separately for each dated slot.
Unknown capacity is not zero. Existing commitments above working time are a finding.
An explicitly complete empty availability list means no available time in the window.

Prioritized work consumes the assigned owner's earliest documented slots. Effort is
divisible into blocks and may span dates. This does not solve meeting duration,
dependencies, travel, client availability or calendar optimization. No reassignment
occurs. Partial allocation never claims completion. Completion later than the deadline
is a deadline-miss finding; future capacity cannot cure a past deadline. Unknown effort,
blocked actions, reported effort and known unallocated minutes remain separate.

## Cohort and economic identities
Starting cohort: joined before period_start and not departed before period_start.
Retained starting cohort: those still present after period_end. A departure on the
closing date counts as departed. A joiner on the opening date is a new relationship,
not part of the opening cohort. Retention = retained starting / starting, only with
complete sourced population and known relationship dates; zero denominator is null.
List all members so denominators can be inspected. This measures the supplied dated
relationship convention, not revenue retention or a predicted outcome.

Economic records must exactly cover households overlapping the measurement period,
including departures. All records share the period, USD and a supplied definition
version. For each household and the reconciled book:

`closing = opening + external inflows - external outflows + internal net transfer + market change - fees debited`

Internal transfer is signed and must net to zero across a complete book. A closing
bridge or book transfer difference larger than one cent produces a finding. Known
values remain visible even when a bridge fails; they are supplied components requiring
review. Net external flow = external inflows - external outflows. Revenue is explicitly
recognized revenue supplied by the practice. Direct contribution = recognized revenue
- supplied direct service cost; it is not fully allocated profit. Fees debited and
recognized revenue are separate fields; neither substitutes for the other.

Calculations use Decimal values before display rounding to cents, HALF_UP. Numbers
may have at most eight decimal places; money is displayed as decimal strings. A
missing component is unknown, not zero. Field completeness is independent: missing
revenue need not hide supported flows. No investment return, organic-growth rate,
attribution, forecast, fee accrual or tax measure is manufactured. If economics is
explicitly not supplied, retain its reason and null measures while completing supported
service work; economics absence alone need not block that narrower review.
