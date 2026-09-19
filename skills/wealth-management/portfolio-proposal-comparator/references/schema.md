# Comparison schema v0.2

Use the common wealth-p0-v1 envelope with source registry, request/household, ISO review date and
US professional capacity. Numbers are finite nonnegative JSON numbers; missing/null numeric or
boolean material facts are unknown. v0.1 proposals require source-backed migration, not defaults.

- `policy`: policy_id, version, owner, source_ids; max_issuer_weight, max_sector_weight,
  max_illiquid_weight (fractions0..1), liquidity_horizon_days, annual_cost_limit_bps. No defaults.
- `proposals`: at least two unique proposal_id records; currency, positive portfolio_value,
  advisory_fee_bps, custody_fee_bps, other_annual_cost_bps, transaction_cost_amount, source_ids,
  holdings. Optional reported_first_year_cost_amount is checked against computed components.
- Each holding: unique holding_id, security_id, weight (fraction0..1), expense_ratio_bps,
  liquidity_days, proprietary, revenue_sharing, cheaper_share_class_available and source_ids.
  The last three are booleans/null. Optional market_value is checked against weight × portfolio_value.
- `exposures` on each holding: list of unique exposure_id records containing constituent weight
  within the holding, issuer_id, sector, asset_class and source_ids. Direct holdings also need a
  sourced constituent row of weight1; a fund needs actual look-through records. Empty/absent/null
  exposures means unknown. Cash, sovereign and other exposures need explicit identifiers/classifications;
  no text labels exempt them from arithmetic or supply an unstated issuer policy exception.

Holdings must sum to one. Constituent weights must sum to one within each holding. Partial look-through
retains only known exposure contributions; overfilled constituent rows are excluded from exposure
totals and flagged. Never normalize either set. A source gap prevents that holding/constituent from
contributing to supported coverage. Unknown maximums remain null while known lower bounds are visible.

Output result: input_snapshot, proposals with metric/coverage/holding registers, symmetric pairwise
differences in input order, selected_proposal:null, tax_estimate:null and scope. Every economic value,
coverage, unknown, finding and hash is reconstructed by the output validator; extra decision fields fail.


## Required upstream issue contract
`upstream_issues` is an explicit list of `{artifact_id, code, message,
status: unresolved|resolved, source_ids}`. Identifiers and message must be nonempty strings;
source_ids must be a list resolving to the envelope registry. Missing/malformed issue structures
reject input; missing/unknown citations remain source-gap findings. Any unresolved issue forces
needs-data regardless of local arithmetic or model consistency. Resolved records remain in the
result and handoff context; status is a supplied reviewer representation, not authenticated closure.
Use an empty list only after reviewing the originating artifacts for material unresolved concerns.

Output `result.upstream_issues` and `result.handoff_context.upstream_issues` preserve every record;
the context also preserves household, date, capacity and source registry. Original code and artifact
identity accompany propagated findings. Recomputing output detects omitted issues/context relative
to the held input. It cannot detect a consistently rewritten source artifact or falsely claimed resolution.
Top-level `unresolved_issues` from another schema is rejected until explicitly mapped; it is never
silently ignored. Earlier draft inputs without this list require source review before migration.
