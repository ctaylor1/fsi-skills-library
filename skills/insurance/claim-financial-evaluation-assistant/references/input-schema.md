# Native input and output contract

Top level: `case_id`, calendar `as_of`, `context` with capacity, represented_party,
object_id, jurisdiction and line_of_business, versioned `sources`, explicit
`unresolved_issues`, optional `upstream_artifacts`, `rule_profile`, and native `data`.
Each source has source_ref and version, with optional source as_of. Duplicate source
IDs reject; distinguish versions explicitly. All domain evidence rows reference the
source registry through source_refs. Missing business amounts are JSON null; numeric
strings or numbers must be finite. Booleans are not monetary numbers.

Rule profile: profile_id, version, source_refs, effective_from, effective_to,
jurisdictions and lines_of_business. The profile is supplied reviewed evidence, not
a built-in legal opinion. Dates must be YYYY-MM-DD. The complete example documents
native field names and supported enums alongside the method reference.

Output: standardized case/context/as_of, source_document, findings, native results,
status, completeness, evaluability, unresolved_issues and insurance artifact. Status
ready-for-review is a draft readiness state only. Null means unknown/unavailable,
not zero. Review findings may exist in an otherwise evaluable draft. No output
selects a professional outcome or executes an action.

## Native `data.position` contract

Supply a `position` object describing one claim at one valuation date and currency.
All four financial amounts are nonnegative finite numbers or decimal strings:

| Field | Contract |
| --- | --- |
| `currency` | Nonblank currency label. Every scenario must match it exactly; currency conversion is not performed. |
| `valuation_date` | Calendar date no later than the top-level review `as_of`. |
| `basis` | Must equal `gross_direct`. Other or missing basis creates a gap. |
| `paid_indemnity` | Indemnity paid to date; a cumulative flow. |
| `paid_expense` | Claim expense paid to date; a separate cumulative flow. |
| `case_outstanding_indemnity` | Current unpaid case indemnity reserve balance; not cumulative paid/incurred. |
| `case_outstanding_expense` | Current unpaid case expense reserve balance. |
| `source_refs` | Nonempty registered ledger/valuation evidence. |

Missing/null amounts remain unknown. Explicit zero is required for a genuinely
zero balance. Negative, boolean, malformed and nonfinite amounts reject. An omitted
position object becomes an incomplete empty position; null is not the supported
object shape. Missing date/currency or future valuation and absent/unresolved/future-
dated source evidence block derived position totals and all scenario computations.
Malformed non-null dates reject. A profile gap separately downgrades the draft; it
does not necessarily suppress otherwise source-supported scenario arithmetic.

## Native `data.scenarios` contract

Supply a nonempty array of scenario objects. Omission/empty array creates a scenario
gap; null is not supported. Each row contains:

| Field | Contract |
| --- | --- |
| `scenario_id` | Required unique nonblank string; missing or duplicate IDs reject. |
| `currency` | Exact match to position currency. |
| `basis` | Must equal `additional_unpaid`. Future amounts exclude paid amounts and are alternative estimates of the unpaid obligation already represented by current case balances. They are not added on top of case balances. |
| `future_indemnity` | Nonnegative additional unpaid indemnity under this scenario. |
| `future_expense` | Nonnegative additional unpaid expense under this scenario. |
| `expected_recovery` | Nonnegative recovery estimate on the scenario's documented scope and timing; null is unknown, not no recovery. |
| `recovery_basis` | Must equal `separate_not_offset`. Gross costs and recovery remain separately identified before a net scenario view is calculated. |
| `assumption` | Nonblank description of the reviewed settlement/liability/expense and recovery assumptions underlying this scenario. |
| `source_refs` | Nonempty registered supporting evidence and assumption references. |

The three scenario amounts follow the same finite/nonnegative/null rules as the
position. Missing assumption, source or amount, mismatched currency, unsupported
basis or incomplete position makes that scenario `not_evaluable` and its computed
fields null. Other valid scenarios may remain evaluable; do not discard the gaps
in the overall artifact. Recoveries exceeding gross scenario totals create a review
finding, rather than silently clipping recovery or selecting a different scenario.

## Native results and arithmetic

`current_position` contains the four supplied balances as six-place decimal strings
(or null) and, when usable, reported incurred indemnity = paid indemnity + outstanding
indemnity and reported incurred expense = paid expense + outstanding expense.

Each output scenario retains its supplied fields, adds `assessment` (`evaluable` or
`not_evaluable`) and these six-place decimal-string results, or null:

- `projected_gross_total_indemnity` = paid indemnity + scenario future indemnity.
- `projected_gross_total_expense` = paid expense + scenario future expense.
- `proposed_change_in_case_indemnity` = future indemnity − current outstanding indemnity.
- `proposed_change_in_case_expense` = future expense − current outstanding expense.
- `net_scenario_total` = both projected gross totals − expected recovery.

Negative proposed changes mean the hypothetical scenario is below the current
case estimate; they are not a booked release. `selected_case_reserve` and
`settlement_recommendation` stay null, and `financial_entries_posted` stays false.
