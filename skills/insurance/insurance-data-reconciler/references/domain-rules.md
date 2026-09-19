# Insurance data reconciliation rules

The firm supplies definitions, comparison scope and versioned configuration. These deterministic checks detect evidence gaps; they do not establish source authenticity, correct records or certify actuarial results.

## Input schema and comparability

Use `as_of`, `config_version`, `current[]`, optional `prior[]`, `expected_periods[]`, optional `expected_series[{key,metric}]`, and `config{movement_pct,definition_baseline_version}`. Every row has `key`, `metric`, `period`, finite `value`, `source_ref`, `definition_version`, `currency`, `unit`, `financial_basis`, `date_basis`, `valuation_date`, and optional `documented_reason`. Context and versioned source declarations follow [insurance-contract.md](insurance-contract.md).

The row grain is `(key, metric, period)`. A comparison requires exactly one current and one prior row, and identical definition, currency, unit, gross/net/ceded basis, date basis and valuation date. This implementation compares like-for-like snapshots; it does not perform actuarial development across valuation dates or infer an FX conversion. Route those transformations to a separately specified method. Missing basis fields make that comparison not evaluable. Signed finite values remain valid for adjustments; missing, boolean, NaN and infinity are rejected.

## Breaks and check coverage

| Break | Meaning |
|---|---|
| `duplicate`, `duplicate_prior` | Ambiguous rows; affected comparisons withheld, never last-row-wins |
| `missing_period` | Declared expected period absent from a known/declared series |
| `missing_current` | Prior observation has no current counterpart; absence is not zero |
| `definition_shift` | Row definition differs from explicitly configured baseline |
| `not_comparable` | Current/prior financial or definition basis missing or different |
| `unexplained_movement` | Comparable finite movement exceeds configured percentage and has no documented explanation |
| `movement_from_zero` | Explicit zero prior changed; absolute movement reported, percentage undefined |
| `new_series` | Current observation has no prior counterpart in a supplied prior dataset |

Duplicate breaks retain every member's source reference, value, side and comparison basis in `observations`. When a duplicate group has prior counterparts, missing or differing bases across all current/prior members also produce a `not_comparable` break. This is a group-level evidence check, not selection of a preferred record or a numeric comparison. Definition-baseline checks inspect every current row, including nonfirst duplicates. Movement remains withheld until exactly one comparable record exists on each side.

`expected_series` can identify a series wholly absent from both snapshots. Without a declared universe, no checker can prove all missing series were found. Without expected periods or prior observations, the respective checks explicitly remain not evaluable. A break is not proof a source value is wrong.

## Output

Per-check states, comparison basis and source references accompany break counts. `clean` requires all declared checks evaluable, no breaks and complete context/provenance; `breaks-for-review` can coexist with partial evaluation; `partial-not-evaluable` prevents absent evidence from appearing clean. The content-bound artifact preserves unresolved issues and declares no approval or execution.

The default 20% movement threshold is a synthetic repository configuration, not a regulatory standard. Replace it with a versioned firm-approved policy appropriate to the metric.
