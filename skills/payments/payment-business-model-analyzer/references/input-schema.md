# Native input schema

Shared envelope: schema_version `1.0`, request_id, as_of (ISO date), jurisdiction `US|EA|UK`, participant (opaque assessed entity), requested_action `analyze|draft`, sources `[{source_id,reference,as_of,review_due?}]`, upstream_issues `[{code,message,source_ids?}]`, and data below. All source_ids reference registered IDs. Dates are Gregorian ISO dates; amounts are decimal strings or integers, never binary floating point or booleans. Null preserves missing evidence. Every record described as sourced requires a nonempty source_ids list. No embedded secret or card-authentication data.

Input validates shape and reference identity. Analysis detects applicability, economic consistency and missing evidence. Output contains source_snapshot, recomputation hash, result, findings, unresolved upstream issues and draft-only handoffs. Always validate output with the independent input path; rehashing arbitrary source changes is not authentication.

## data

analysis_question and accountable_owner are required text. companies, segments, comparisons and strategic_options are explicit sourced lists; the first two cannot be empty. Each row has source_ids and unique identity within its list.

companies: company_id; nonempty roles list from issuer, acquirer, processor, scheme, gateway, orchestrator, merchant, platform, wallet, bank, agent, infrastructure-provider; customer; value_proposition; monetization; dependencies; jurisdiction. Company IDs represent the perimeter of analysis, not necessarily the entire consolidated group.

segments: segment_id, company_id, economic_partition_id, segment_name, currency, period_start, period_end, period_basis, volume_definition, scope_definition, accounting_policy_ref, volume_unit (currency-amount|transaction-count|unknown), revenue_basis (gross-billings|net-revenue), costs_complete boolean. Actual periods must end on/before as_of. economic_partition_id identifies nonoverlapping economic coverage; overlapping dates for the same company/partition/currency are ambiguous, including aggregates plus components. Assigning unrelated partition labels does not prove disjointness; mapper must review raw source totals.

Explicit numeric fields (amount or null): payment_volume, gross_billings, pass_through, incentives, reported_net_revenue, variable_cost, allocated_fixed_cost. Only reported_net_revenue permits signed amounts; others are nonnegative. A transaction-count or unknown volume_unit suppresses net take rate. With volume_unit currency-amount, payment_volume is currency-denominated eligible processed/settled/sales volume as explicitly defined, never a transaction count. All financial fields use this row's currency/period. Pass-through and incentives are disjoint reductions from gross billings; variable costs exclude amounts already passed through. For gross-billings, net is gross minus both reductions; a supplied reported_net_revenue must reconcile. For net-revenue, take reported_net_revenue as already after pass-through/incentives; optional complete gross bridge must reconcile. Net may be negative. Unknown reductions prevent a gross bridge; reported net does not require a second subtraction.

comparisons: comparison_id, left_segment, right_segment, accounting_comparability_review_ref (missing yields gap), source_ids. The helper compares only same currency, exact period, period_basis, volume_definition and scope_definition, plus known net take rates. It does not annualize, convert FX, merge companies or infer comparable accounting from labels. The review must assess principal/agent and gross/net presentation, refunds, incentives, acquisitions, geography, product mix and definitions.

strategic_options: option_id, hypothesis, test, owner, dependency, risk, nonempty segment_ids and source_ids. Every hypothesis remains for owner review and approved false. Unknown segment links generate a gap. This records proposed tests, not forecasts or authoritative recommendations.

## result

Value-chain company rows are retained. Each segment yields known net_revenue, net_take_rate_bps (`net / positive payment_volume * 10000`), contribution_before_fixed (`net - complete variable_cost`), contribution_after_allocated_fixed (`prior - allocated_fixed_cost`) or null. Negative results are retained. Division by zero produces a gap and null. Neither contribution measure is accounting profit. Comparison deltas require comparable_on_supplied_basis; larger take rate is not presumed better. cross_currency_total is always null. No securities recommendation or strategy approval occurs.
