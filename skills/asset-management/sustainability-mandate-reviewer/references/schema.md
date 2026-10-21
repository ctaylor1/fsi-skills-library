# Native schema

Use the foundation fields request_id, object_id, as_of, knowledge_cutoff, currency, audience=`internal-review`, sources and optional unresolved_issues. Every source needs source_ref, version, as_of and known_at; every domain row below has a unique ID and eligible registered source_ref. Dates are real YYYY-MM-DD values. Collections have at most 10,000 rows. Numeric inputs are finite decimals within the shared 38-digit/exponent bounds; prefer strings for exact source precision.

| Object / row | Required fields |
| --- | --- |
| mandate | mandate_id, version, owner, reviewer, review_status, effective_from/effective_to inclusive, source_ref |
| portfolio | snapshot_id, valuation_date equal to as_of, currency equal to request, total_market_value, source_ref |
| holdings / holding_id | instrument_id, issuer_id, snapshot_id, currency, nonnegative market_value, boolean metric_eligible; ineligible holdings also need exclusion_basis |
| metrics / metric_id | definition, definition_version, unit, owner, denominator_basis=`total-market-value` or `eligible-market-value`, required_vintage integer calendar year, estimates_allowed boolean, minimum_coverage fraction [0,1], operator<=/>=, nonnegative limit |
| observations / observation_id | holding_id, metric_id, unit, definition_version, observed_on, vintage, estimated boolean, nonnegative value or explicit null |
| exclusions / exclusion_id | metric_id, operator< / <= / > / >=, nonnegative threshold, owner |

Holdings and metrics are nonempty. Observations/exclusions are explicit lists and may be empty. Duplicate holding/metric observations fail rather than choosing a vendor or revision silently. Holdings must reconcile exactly to the portfolio total. Mixed currency, incompatible units/definition versions, future-known observations or negative positions/metrics fail input validation. Wrong vintage, disallowed estimates, missing values, missing mandate review and ineffective terms retain issues and withhold full conclusions.

Results include denominator amounts, eligible/covered/estimated market values, coverage fractions, full weighted_metric when evaluable, a separately labeled covered_only_mean, unavailable observations, exact-limit decisions, and per-exclusion breached/unknown holding IDs and exposure. Ratio displays round to 12 places; comparisons use exact cross-multiplication. No score, label, compliance certification or execution authority is emitted. Output validation requires the detached original input.
