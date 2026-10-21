# Native input schema

The common `compliance-foundation/2.0` envelope is specified in the bundled foundation contract.
The `data` object contains exactly the following native records.

review: product, distribution_role, window_from, window_to, metric, expected_cohorts; cohorts[]: cohort_id, population, observed, harms, vulnerable, value_barriers, support_barriers, threshold_rate. Fields are facts; counts are nonnegative integers or null, harms <= observed <= population when all known. Expected groups missing from rows remain unresolved. No weighted universal conduct score.

A fact holds `value`, `source_refs` and `fact_ids` under the common contract; use null with explicit unknown/conflict source status when unavailable. Match exact value and type to the mapped source fact, including empty/zero/false facts. Identity values are not interchangeable across cases. Unknown fields and malformed dates/counts stop intake. Substantive missingness proceeds only as an unresolved draft.

Native object_type: `customer_conduct_review`. The executable `domain.py` schema is authoritative for the exact required fields/types; all data record IDs are internal labels, and consequential identity/context values are claims.

## Complete field inventory

Each listed consequential field is an exact claim object `{value, source_refs, fact_ids}`.
Only the row label named below is a plain internal ID. Empty evidence-reference lists preserve
unknowns; malformed types/fields stop intake.

- `data.review`: `product`, `distribution_role`, `window_from`, `window_to`, `metric`, `numerator_definition`, `denominator_definition`, `segmentation_basis`, `vulnerability_method`, `expected_cohorts`.
- `data.cohorts[]`: row label `cohort_id`; claims `population`, `observed`, `harms`, `vulnerable`, `value_barriers`, `support_barriers`, `threshold_rate`.

## Typed count units and supported metric

Supply source-bound `review.population_unit`, `review.numerator_unit` and
`review.denominator_unit` claims. The bounded method supports binary affected-customer
proportions with all three equal to `unique-customers`. Repeated event counts are not
affected customer counts; event/customer, account/customer and other unit combinations
are unsupported and withhold rates and thresholds. Missing units remain a valid
partial intake with unknown metrics; never infer units from prose. Threshold comparison
uses the exact count ratio against the supplied decimal threshold; displayed rounding
does not turn an exception into acceptance.

Decimal `threshold_rate` values must be source-bound decimal strings (for example,
`"0.05"` or `"0.33333333333333333334"`), with the same string in the cited source
fact. The string contains digits with an optional decimal point, is at most 256
characters and lies in [0, 1]. Integer 0/1 thresholds are also exact. JSON fractional
numeric thresholds remain valid partial intake, but their original decimal precision
cannot be established after floating-point parsing; criterion comparison is withheld
and the output requests exact decimal evidence. Displayed rates do not determine
acceptance.
