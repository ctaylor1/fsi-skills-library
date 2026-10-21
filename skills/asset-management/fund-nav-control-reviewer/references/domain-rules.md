# Bounded Phase 1 method

All comparisons use exact Decimal strings. Rows with wrong source, missing units/currency/class/basis, invalid/future/stale dates or ambiguous multiplicity are retained as not_evaluable; overall status is needs_data. Cutoff is the exact requested valuation date; different dates never imply clears-next-cycle. Class/unit controls remain separate. Difference = classified break impact + explicitly recorded within-tolerance difference + residual. Missing-price as well as price-disagreement routes to fund-valuation-oversight-reviewer. expected_components defines the bounded review universe; omitted categories are not inferred complete. No NAV/share, asset valuation, fee engine, posting, official strike or certification is supplied.

This is an offline draft evidence method, not a production source of record. Read [schema](schema.md) before mapping inputs. Native output is reconstructed from the separately retained input; independent expected results and professional review remain necessary.

## Supported decimal bounds

Supply decimal strings when every input digit matters. Each numeric input supports at most 38 coefficient digits (including retained trailing zeros), a Decimal exponent between -38 and +38, and a nonzero adjusted exponent between -38 and +38. Numeric literals are limited to 256 characters; booleans and non-finite values are rejected. The job supports at most 100,000 total input records/lines. Amounts, tolerances, materiality thresholds and supplied FX rates use these bounds. Unsupported values fail before a result is emitted.

All arithmetic, including aggregation, differences, tolerance/materiality checks and any FX multiplication, uses a private 256-digit Decimal context with inexact/rounding traps. The process-global context is unchanged. Derived results can contain more than 38 digits; the input limits plus row bound make the supported operations exact within the working context. These are software precision limits, not instrument conventions or economic materiality policies.
