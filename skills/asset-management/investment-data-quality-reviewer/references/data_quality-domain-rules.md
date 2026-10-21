# Bounded Phase 1 method

Held instruments without any price row produce missing_price. Invalid/future price dates produce temporal_invalid and withhold dependent price tests. Calendar-day staleness is explicit. Price movement is evaluated only with dated, reviewed comparability (including corporate actions, currency and units). Factor age defaults to 30 calendar days; absent/invalid/stale factor evidence remains unresolved. Ticker collisions require supplied exchange and currency. Classification conflicts require two feeds with the same effective date. Unknown NAV impact is never inferred. Severity/default thresholds are bounded library conventions, not regulatory limits.

This is an offline draft evidence method, not a production source of record. Read [schema](data_quality-schema.md) before mapping inputs. Native output is reconstructed from the separately retained input; independent expected results and professional review remain necessary.
