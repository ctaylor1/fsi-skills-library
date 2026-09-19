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

## Native `data` fields

Use one experience cohort, one currency and one exposure unit. Required sections
for an evaluable indication are `premium`, `losses`, `exposure` and `assumptions`,
each an object. An omitted section is treated as empty and yields data gaps; null
is not the supported object shape. See the method reference for the formula and
professional selection responsibilities.

| Field | Contract |
| --- | --- |
| `period_start`, `period_end` | Experience-cohort dates; start must be on or before end. |
| `premium.amount` | Positive historical earned premium before the supplied on-level and premium trend adjustments. |
| `premium.currency` | Nonblank currency label; exact match to loss and assumption currency required. Normalize source codes before constructing the input; the helper does not validate an ISO currency registry. |
| `premium.basis` | Must equal `earned`. |
| `premium.period_start`, `premium.period_end` | Must exactly match the cohort dates. |
| `premium.source_refs` | Registered versioned premium evidence. |
| `losses.amount` | Nonnegative reviewed ultimate non-CAT loss plus LAE for the same cohort. This is not paid loss or a case-reserve balance. |
| `losses.currency` | Must match premium currency. |
| `losses.basis` | Must equal `ultimate_loss_and_lae`. |
| `losses.period_start`, `losses.period_end` | Must exactly match the cohort dates. |
| `losses.source_refs` | Registered evidence for the ultimate-loss/LAE selection and its basis. |
| `exposure.amount` | Positive earned exposure for the cohort. |
| `exposure.unit` | Nonblank unit, such as `building-year`; exact match to assumption exposure unit required. |
| `exposure.period_start`, `exposure.period_end` | Must exactly match the cohort dates. |
| `exposure.source_refs` | Registered exposure evidence. |

The `assumptions` object contains every field below unless specifically conditional:

| Field | Contract |
| --- | --- |
| `currency`, `exposure_unit` | Match the currency and exposure unit above. |
| `on_level_factor` | Positive multiplier adjusting historical earned premium to the reviewed common rate level. |
| `premium_trend_factor` | Positive prospective premium multiplier. |
| `loss_trend_factor` | Positive prospective loss/LAE multiplier. |
| `credibility` | Number in `[0,1]`; use decimals, not percentage points. |
| `complement_loss_and_lae_per_exposure` | Nonnegative prospective complement. Required when credibility is below 1; omitted or unused when credibility equals 1. It shares the loss/CAT basis and units of the experience estimate. |
| `fixed_expense_per_exposure` | Nonnegative prospective fixed expense per exposure. |
| `variable_expense_ratio` | Number in `[0,1]`. |
| `profit_ratio` | Number in `[0,1]`; sum with variable expense ratio must be less than 1. |
| `catastrophe_provision_per_exposure` | Nonnegative separate prospective CAT provision. Explicit zero is required when the reviewed provision is zero. |
| `catastrophe_basis` | Must equal `excluded_from_losses`; avoid counting CAT costs again in losses or credibility complement. |
| `reinsurance_net_cost_per_exposure` | Finite signed prospective net cost after expected recoveries; not ceded premium alone. A negative value requires a documented consistent net-cost basis. |
| `reinsurance_basis` | Must equal `net_cost_after_expected_recoveries`. |
| `alignment_reviewed` | Supply JSON `true` only for a documented reviewed alignment of periods, coverage, exposure and adjustment assumptions. |
| `source_refs` | Nonempty registered evidence for selections, dates, methods and bases. |

Numeric values can be finite JSON numbers or decimal strings. Missing/null required
numbers remain unknown and suppress the indication; they do not become zero.
Negative values reject except for the signed reinsurance net-cost field. Booleans,
nonfinite values and numbers outside bounded ratios reject. Zero premium, exposure
or trend/on-level factor, or a nonpositive expense/profit denominator, produces a
data-gap result with null indication. Malformed dates reject; missing dates,
period/currency/unit/basis mismatch, absent or future-dated source evidence, and a
missing/inapplicable profile suppress calculation. The final indicated cost must
not be negative.

## Native results

`method` is `single_cohort_pure_premium_indication`. Five computed fields are
`current_adjusted_premium_per_exposure`, `experience_loss_lae_per_exposure`,
`credibility_blended_loss_lae_per_exposure`, `indicated_premium_per_exposure` and
`indicated_change`. They are decimal strings rounded to six places, or null when
the native calculation is unavailable. `indicated_change` is a decimal ratio, so
`0.10` means 10%. Currency, exposure unit and supplied assumptions are retained.
`rate_selection` remains `not_performed`; `filing_approval` remains `not_determined`.
The foundation can additionally downgrade overall status for inherited evidence
gaps; a numerical indication does not remove those gaps.
