# Native event intake

Use `schema_version: ir-phase3-event/1.0` and the common supplied-evidence fields
shown in `evals/files/input.json`: request/subject, as-of/use dates, knowledge
cutoff, information barrier, sources, precise `evidence_refs` and inherited
`unresolved_issues`. Subject is one issuer or security. A security also requires
its issuer ID. Public readers reject duplicate JSON keys and non-finite numbers.

`financial_basis` requires `currency` (three uppercase letters), `units`,
`share_units`, `accounting_basis` and `consolidation_scope`. Money and share scales
must match (`ones`, `thousands`, `millions`, `billions`); price is currency per
individual share. No FX or unit conversion occurs. `valuation_subject` identifies
`security_id`, `share_class` and `share_count_basis`; it must match a security
subject. Use the same supplied security/class/basis for existing and new shares.
Other classes or ownership structures need a reviewed conversion first.

`baseline` requires `balance_date`, `known_at`, nonnegative `cash` and `debt`,
strictly positive `shares` and nonempty `evidence_refs`. Cash is the supplied
available balance, debt is outstanding principal, and shares are the supplied
point-in-time share count on the declared basis. Missing balances are rejected;
they are never converted to zero. `balance_date` must precede the event's
effective date, preventing an already reflected event from being added twice.

`event` requires `event_id`, `type`, `status`, `announcement_date`,
`effective_date`, `known_at`, `scenario_label`, `evidence_refs` and `terms`.
One event is supported per packet. `status` is `proposed`, `announced` or
`completed`. Proposed scenarios have null announcement dates. Announced/completed
events have an announcement date no later than the event knowledge/effective
dates. Completed terms require effective date no later than as-of and event
knowledge, and a null scenario label. Pending events require a meaningful
scenario label. Completion metadata are supplied assertions, never authenticated
legal conclusions. An elapsed expected effective date does not imply completion.

Both baseline/event `known_at` must be known by the cutoff and as-of day. Each
row's cited source must be known by that row's asserted knowledge. Date precision
must match for these comparisons; a date-only source is not assigned midnight to
fit a timestamp cutoff. All row citations must be declared in top-level citations
so the canonical permissions and source-identity gate sees them.

The following exact `terms` fields are required, including explicit zero fees or
zero financing components. Unknown/extra fields are rejected so ignored inputs
cannot silently change the economics.

| Type | Required numeric terms |
| --- | --- |
| `equity-raise` | `shares_issued`, `issue_price`, `fees` |
| `share-repurchase` | `cash_spend`, `repurchase_price`, `fees`, `cash_funding`, `debt_funding` |
| `acquisition` | `purchase_equity_value`, `target_debt_assumed`, `acquired_cash`, `debt_funding`, `equity_funding_shares`, `issue_price`, `cash_funding`, `fees` |
| `refinancing` | `principal_repaid`, `new_debt_proceeds`, `fees`, `cash_funding`, `cash_retained`, `old_annual_rate`, `new_annual_rate` |
| `asset-disposal` | `sale_cash_proceeds`, `debt_transferred`, `cash_disposed`, `fees`, `taxes` |

All values are finite nonnegative numbers, never booleans. Shares/prices for an
equity raise, repurchase spend/price, acquisition purchase price and refinanced
principal exceed zero. Refinancing rates are annual fractions between zero and
one, used as fixed supplied rates for the replaced/new tranches only. No rates
are fetched or forward curves inferred. An acquisition with zero stock funding
requires an explicit zero issue price. Debt repaid/transferred cannot exceed
baseline debt, disposed cash cannot exceed baseline cash, and repurchases must
leave positive shares outstanding. Fees cannot exceed equity-raise proceeds.

`results` contains `event_summary`, `effect_basis`, `financial_bridge`,
`event_metrics`, `funding_reconciliation`, `review_limitations` and explicit
nonverification flags. Before/change/after bridge fields are `cash`, `debt`,
`shares`, `net_debt`. Funding separately reports `upfront_cash_required`,
`upfront_cash_available_from_baseline`, `upfront_cash_shortfall` and
`ending_cash_shortfall`. Acquisition/repurchase/refinancing `cash_funding` must be
available before acquired cash or retained refinancing proceeds. Both upfront and
ending shortfalls must be zero for `cash_feasible_for_supplied_bridge` to be true;
availability itself remains unverified. `additional_cash_required` is the maximum
of the two shortfalls, avoiding double counting an overlapping gap. Any shortfall
makes the packet partial, even if closing cash is nonnegative. The full original is
required to reconstruct every output field. Ineligible source evidence withholds
the entire projection and lineage. Passing reconstruction confirms supplied
consistency, not source truth, institution acceptance or transaction approval.
