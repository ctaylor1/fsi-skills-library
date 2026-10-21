# Native input schema

Required envelope: `case_id` durable nonblank string; `as_of` YYYY-MM-DD;
`context` object with nonblank `capacity`, `represented_party`, `object_id`,
`jurisdiction`, `line_of_business`; `sources` array of unique objects containing
`source_ref`, `version`, `as_of`, `locator`; `unresolved_issues` explicit string
array; `data` object. Source dates must be no later than as_of. Unknown context may
be the literal unknown and keeps the result partial. No extra field grants authority.

`data.owner`, `market`, `program`, `product`, `source_locator`, `inventory_statement`,
`reviewed_by`, `reviewed_on` and `source_refs` are required. The statement must
expressly support the completeness/review claims and name the inventory scope;
review dates cannot postdate as_of. Source references resolve to the envelope and
locators identify evidence within those sources. A reviewer name does not prove
review. Model extraction must preserve null where the raw source is silent.

The profile is **data.profile**, never top-level. It requires `profile_id`,
`version`, `reviewed_by`, `source_refs`, `method`, inclusive `effective_from` and
`effective_to` around as_of, `jurisdictions` including context.jurisdiction,
`lines_of_business` including context.line_of_business, `markets`, `programs`,
`products` including actual data values, `rule_basis`, and `limitations`. Arrays
are explicit strings. These are supplied scope evidence, not adopted rule packs.

All fields below are required except an explicit optional field or conditional
field. Text is nonblank; no unknown/n/a substitute establishes evidence. Dates are
YYYY-MM-DD. Numeric values use finite exact decimal strings or integer JSON numbers;
fractional JSON floats, booleans and NaN/infinity are rejected. Numeric null means
unknown, never zero. Values are nonnegative unless expressly signed; proportions
are in [0,1]; stated integer fields must be whole. All inventories are arrays of
objects, at most 10000 rows each, with unique nonblank identity fields. Each record
has `source_refs` and `source_locator` unless stated otherwise. An explicit empty
array is different from unknown/null. Evidence gaps preserve a valid needs-data
artifact with dependent results null; malformed types reject input.

Optional `upstream_artifacts` and `context_mappings` use workflow-contract.md.
Unresolved upstream/input issues withhold derived results. Reviewed context mapping
must bind source artifact hash, source_context, target_context, reviewed_by, basis
and source_refs. No mapping removes inherited issues.

## Pricing profile and top-level data

`context.capacity` is exactly `health-pricing-review`, `line_of_business` is
`health`, and `object_id` equals data.cohort_id. data.reviewed_on must be on or
after valuation_date. Numeric inputs support up to 256 significant digits and
exponent magnitude 1000. Exact rational arithmetic prevents intermediate rounding;
terminating decimal outputs are exact and recurring ratios are rendered at 50
significant digits, explicitly labeled in results.


`profile.method` is exactly `reviewed-health-cohort-pricing-v1`; additionally
`profile.currencies` is an explicit array containing the actual currency. Supported
scope uses one currency, cohort, benefit basis and source-reconciled exposure basis.

`data` also contains `cohort_id`, `population_basis`, `currency`, `benefit_basis`,
`period_start`, `period_end`, `valuation_date`, `inventory_complete`,
`adjustments_complete`, `assumptions_reviewed` (boolean or null),
`expected_category_ids` (unique nonempty string array), and the objects/inventories
below. Base start <= end <= valuation <= review as_of. Expected category IDs must
exactly equal supplied categories. All three affirmative flags require the cited
inventory/review statement, including explicit review of an empty adjustment list.

For the table, **scope** means the four fields cohort_id, population_basis, currency,
benefit_basis; **base** means scope plus period_start, period_end, valuation_date;
**projected** means scope plus projection period_start and period_end. Required
repeated fields must exactly equal their governing data/projection fields.

| Object / inventory | Exact required fields and semantics |
| --- | --- |
| `exposure` | base; source_refs, source_locator; `complete` boolean/null; `exposure_unit` exactly `member-months`; `partial_month_method` text; positive `member_months`; positive aligned `earned_premium`. Snapshot enrollment is unsupported. |
| `projection` | scope; source_refs, source_locator; `period_start`, `period_end` future dates with start <= end and start after base end; `trend_from`, `trend_to` dates with from <= to; `trend_basis`, `projection_basis`, `partial_month_method` text; `exposure_unit` exactly `member-months`; `complete`, `population_bridge_reviewed` boolean/null; positive `member_months`, positive `current_premium_pmpm` on this comparable projection population/benefit basis. |
| `categories[]` | unique `category_id`; base; source_refs, source_locator; `complete`, `case_excludes_ibnr` boolean/null; nonempty unique `economic_event_ids`; `incurred_convention` exactly `paid-plus-case-outstanding-plus-ibnr`; `paid`, `case_outstanding`, `ibnr`, `recoveries` amounts; `recovery_basis` exactly `gross-deduct-recoveries` or `net-recoveries-already-included`; positive cumulative `cost_factor`, `utilization_factor`; `trend_from`, `trend_to`, `trend_basis` identical to projection. |
| `adjustments[]` | May be explicitly empty. Unique `adjustment_id`; `category_id` existing category; `economic_event_id` unique across all claim and adjustment events; `stage` exactly `base-incurred-amount` or `projection-pmpm`; `reason`; source_refs, source_locator; signed `amount`. Base stage requires all base fields; projection stage requires projected fields. |
| `expenses` | projected; source_refs, source_locator; `expense_basis` text; `complete` boolean/null; nonnegative `fixed_total` dollars and `pmpm`; `premium_proportion` and `margin_proportion` in [0,1], with sum strictly less than one. Fixed total covers the projection exposure period. |

Claim events cannot appear in two categories or adjustments. Paid net of recoveries
requires recoveries explicitly zero, preventing a second deduction. Outstanding
means unpaid case reserve excluding IBNR; IBNR requires an explicit supplied amount,
including explicit zero, and is never inferred from paid claims. Net incurred and
adjusted/projected claim costs must be nonnegative for this supported method.

`results.metrics` keys are base_member_months, projected_member_months, net_incurred,
adjusted_incurred, projected_claim_pmpm, nonpremium_expense_pmpm,
conditional_premium_pmpm, renewal_change_fraction,
descriptive_incurred_to_earned_premium. All are decimal strings or null.
`results.categories[]` preserves category_id/source_refs and net_incurred,
adjusted_incurred, base_pmpm, projected_pmpm. Currency/cohort are retained.
statutory_mlr_calculated, premium_approved, filing_prepared remain false. Any gap
withholds all derived numeric results; raw inputs remain in source_document.
