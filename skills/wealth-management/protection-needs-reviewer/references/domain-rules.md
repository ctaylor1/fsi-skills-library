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

## Protection domain records

Top-level `currency` is USD. `policy.methodology` must explicitly be `level-undiscounted`.
`policy.required_scenario_types` is a nonempty unique list of survivor/disability/long-term-care/
liability. It defines the requested review scope; no omitted scenario is described as reviewed.

`scenarios[]` contains unique `scenario_id`, `type`, `subject_id`, `description`, `source_ids`,
`assumptions` and an explicit `designated_resources[]`. Each resource has unique `resource_id`
within the scenario, `description`, nonnegative numeric `amount` or null, `availability`
(available-for-scenario/uncertain/unavailable), and `source_ids`. Explicit empty resources means
no designated resources for this scenario; it does not assert the household has no other assets.

Every `assumptions` object has a nonempty `basis` explaining the supplied economic and benefit
applicability assumptions, `source_ids`, and the following type-specific amounts/horizons.
Unknown fields are null; missing required assumptions suppress the entire scenario calculation.
All money amounts are nonnegative finite numbers. Month counts are integers 0–1200;
support years are numbers 0–100. These are supported calculation bounds, not actuarial defaults.

| Type | Assumptions | Gross scenario need and modeled insurance offset |
| --- | --- | --- |
| survivor | annual_spending, annual_survivor_income, support_years, debt_payoff, one_time_costs, life_benefit | max(spending−income,0) × years + debt + one-time costs; offset min(gross, life benefit) |
| disability | monthly_spending, monthly_other_income, disability_months, waiting_months, monthly_benefit | monthly deficit × duration; offset min(deficit, benefit) × max(duration−waiting,0) |
| long-term-care | monthly_care_cost, care_months, waiting_months, monthly_benefit, benefit_month_limit, lifetime_benefit_cap | care cost × duration; eligible months=min(max(duration−waiting,0),month limit); offset=min(min(cost,benefit)×eligible months, lifetime cap) |
| liability | projected_loss, defense_costs, primary_applicable_amount, umbrella_applicable_amount | supplied loss + defense costs; offset min(gross, applicable primary+umbrella amounts) |

The professional supplies benefit applicability and consistent before-/after-tax amounts; no
claim interpretation, exclusion decision, likelihood estimate, expense escalation or assumed
income tax rate is embedded. Survivor income excludes the life benefit that is separately
counted. Designated resources exclude insurance benefits already counted in the assumptions and
must be available in the modeled event. Liability defense treatment is reflected in the supplied
applicable amounts, never inferred from limit labels.

For all types, remaining gap=max(gross−insurance offset−available designated resources,0).
Only explicitly available resources count. Unknown amount/availability or missing assumption
citations suppresses calculation; output retains the evidence and gap. Decimal arithmetic is
rounded half-up to two places only at output. Money results are decimal strings.

## Output interpretation

Each `result.scenarios[]` has preserved assumptions/resources, formula, intermediate steps,
`gross_scenario_need`, `modeled_insurance_offset`, `designated_resource_amount`,
`remaining_scenario_gap`, resource surplus and professional review questions. `calculation` is
null when not evaluable. A calculated positive gap is a scenario result, not a data error or
coverage inadequacy verdict. `review-ready` can therefore include a positive modeled gap.
`resource_reuse` identifies assets designated in more than one alternative scenario;
`portfolio_total` is always null. Never sum scenario needs or count one resource twice within
a concurrent combined event. Joint-event, inflation, discounting and probabilistic analysis need
a separately reviewed method; none is implied by this simple deterministic package.
