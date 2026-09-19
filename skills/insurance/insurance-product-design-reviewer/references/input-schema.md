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

Supply `features` and `requirements` as arrays of objects, including an explicit
empty array when no reviewed rows are available. Omitted arrays act as empty lists
and create the corresponding review-scope gaps. A null array is not the supported
representation. IDs must be unique, nonblank strings within their array; duplicate
or missing IDs reject the input.

| Field | Type and meaning | Missing or unresolved behavior |
| --- | --- | --- |
| `product_name` | Nonblank product label. | Design gap. |
| `target_market` | Nonblank intended customer/market description. | Design gap. |
| `coverage_basis` | Nonblank description of the proposed coverage promise and basis. | Design gap. |
| `distribution_channels` | Nonempty array of nonblank channel descriptions. | Channel gap; channels are not inferred. |
| `features` | Feature evidence rows described below. | Empty or omitted list creates a feature gap. |
| `requirements` | Reviewed requirement assertions described below. | Missing category coverage creates a scope gap. |

Each `features[]` row contains:

| Field | Contract |
| --- | --- |
| `feature_id` | Required unique nonblank string. |
| `promise` | Nonblank customer-facing promise under review. |
| `wording_ref` | Nonblank locator for the relevant supplied wording, such as form/version/section. This is a locator, not a second registry ID. |
| `operational_owner` | Nonblank accountable team or role. |
| `claims_test_status` | `pass`, `fail` or `unknown`. Omission becomes `unknown`; any other value, including null, rejects. A failed test is a review finding; unknown is a data gap. |
| `source_refs` | Nonempty array of registered evidence references covering the feature, wording and operating review. |

Each `requirements[]` row contains:

| Field | Contract |
| --- | --- |
| `requirement_id` | Required unique nonblank string. |
| `category` | Exactly `actuarial`, `wording`, `distribution`, `operations` or `filing`; other or missing values reject. |
| `required` | Required JSON boolean. This is the reviewed applicability assertion, not an inferred legal requirement. |
| `status` | `satisfied`, `unsatisfied` or `unknown`; omission becomes `unknown`. Other values reject. |
| `source_refs` | Nonempty registered evidence references for the applicability and status assertions. |

At least one row from every category is needed to document the complete review
scope. A non-required row can document a reviewed category; the script does not
invent additional requirements. A required, unsatisfied row creates a review
finding; a required, unknown row creates a data gap. Evidence references are still
required for non-required rows.

`null`, blank text and literal `unknown`, `n/a` or `na` do not satisfy the descriptive
text fields. Missing `source_refs`, unresolved references or evidence dated after
`as_of` create gaps. They do not authenticate an otherwise asserted pass.

## Native results

`feature_matrix` preserves supplied rows and adds `traceability` (`complete` or
`partial`), which measures source/wording/owner linkage only. A feature with complete
traceability may still have a failed claims test. `requirement_matrix` retains the
reviewed assertions, and `review_scope` lists represented categories. The fixed
fields are `launch_authorized: false`, `product_approval: not_determined` and
`next_owner: product governance`. These do not change when all supplied tests pass.
