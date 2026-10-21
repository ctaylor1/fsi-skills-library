# Bounded Phase 1 method

Exact Decimal amounts are emitted as strings; no two-decimal rounding of securities. Verify account/type/instrument/currency/unit/basis within match keys. Multiple rows are not duplicates by inference: require explicit sum aggregation or return not_comparable. Declared duplicate_of requires investigation. Missing FX yields material:null and not_evaluable materiality. Settlement dates alone do not establish timing causality; settlement_evidence_ref is required. Proposals present conditional internal/external correction alternatives and unresolved status; no adjustment is selected and no corrected book total is asserted. Within-tolerance differences are explicitly accounted for.

This is an offline draft evidence method, not a production source of record. Read [schema](schema.md) before mapping inputs. Native output is reconstructed from the separately retained input; independent expected results and professional review remain necessary.

## Supported decimal bounds

Supply decimal strings when every input digit matters. Each numeric input supports at most 38 coefficient digits (including retained trailing zeros), a Decimal exponent between -38 and +38, and a nonzero adjusted exponent between -38 and +38. Numeric literals are limited to 256 characters; booleans and non-finite values are rejected. The job supports at most 100,000 total input records/lines. Amounts, tolerances, materiality thresholds and supplied FX rates use these bounds. Unsupported values fail before a result is emitted.

All arithmetic, including aggregation, differences, tolerance/materiality checks and any FX multiplication, uses a private 256-digit Decimal context with inexact/rounding traps. The process-global context is unchanged. Derived results can contain more than 38 digits; the input limits plus row bound make the supported operations exact within the working context. These are software precision limits, not instrument conventions or economic materiality policies.
