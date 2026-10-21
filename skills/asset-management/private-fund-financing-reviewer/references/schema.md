# Native schema

Common fields: `request_id`, `object_id`, real-date `as_of` and `knowledge_cutoff`, `currency`, `audience: internal-review`, versioned `sources` (`source_ref`, `version`, `as_of`, `known_at`) and `unresolved_issues`. Every agreement, facility, collateral and concentration record has an eligible registered `source_ref`. Source declarations are not authenticated. Monetary inputs share the request currency. Use decimal strings; missing numbers, booleans and nonfinite values fail. Numeric domain: up to38 significant digits/exponent magnitude38; collateral limit10,000 rows.

`mode`: `subscription` or `nav`.

`agreement`: `version`, `reviewed_by`, `effective_from`, `expires`, `currency`, `facility_type` matching mode, `concentration_method: fixed-pre-cap-credit-base`, `proceeds_assumption`, nonempty `permitted_proceeds` list, nonnegative `maximum_facility_debt`, `maximum_fund_debt_to_nav` between0 and10.

`facility`: `id`, matching `agreement_version`, `maturity_date`, `proposed_draw_date`, `proceeds_use`, `cost_assumption`; nonnegative `commitment_limit`, `outstanding`, `proposed_draw`, `letters_of_credit`, `reserves`, `other_fund_debt`, `upfront_fee`; strictly positive `fund_nav`; `interest_rate` and `undrawn_fee_rate` between0 and1; integer `accrual_days` from0 through3660; `day_basis`360 or365. Subscription mode also requires `total_uncalled_commitments`. `other_fund_debt` excludes this facility's drawn balance; LC/reserves consume credit availability but are not counted as funded debt in this explicitly bounded leverage measure.

`collateral`: nonempty unique `id`, `agreement_version`, `currency`, `concentration_group`, boolean `eligible`, `eligibility_reason`, `haircut` and `advance_rate` between0 and1. Subscription rows contain nonnegative `uncalled_commitment` and cannot contain `nav`; NAV rows contain nonnegative `nav` and cannot contain `uncalled_commitment`. Include ineligible rows so all raw collateral reconciles to `total_uncalled_commitments` or `fund_nav` respectively.

The proposed draw must also fall within the reviewed agreement effective interval; a later facility maturity does not extend expired agreement evidence. An out-of-period draw remains an explicit review issue.

`concentration_limits`: one record for every collateral group, with `group`, `agreement_version`, `maximum_fraction` between0 and1 and `source_ref`. Caps reference the fixed total eligible credit after haircut and advance rate, before concentration deductions. Other legal definitions are unsupported.

`inventory_complete` and `inventory_source_ref` declare register completeness. Missing completeness or a total mismatch withholds borrowing-base and borrowing-base-dependent headroom; supplied covenant analysis remains qualified by unresolved issues.

Output uses `investment-foundation/1.0`: source-bound draft with collateral/group bridges, usage, separate commitment/base/covenant headroom, leverage, costs, issues and fixed `borrowing_authorized: false`, `lender_certificate: false`. Detached output validation reconstructs every field. No implicit FX, netting, PIK or hybrid basis exists.
