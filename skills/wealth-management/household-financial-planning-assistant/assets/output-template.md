# Household planning discussion — {{artifact_id}}

As of {{as_of}} · Capacity {{engagement.capacity}} · Mode {{result.mode}} · USD
Status {{status}} · Human review required · Draft only · Not delivered

## Monthly cash flow and commitments

| Net income | Living expenses | Debt service | Reserve contribution | Surplus before goals | Goal contributions | Remaining |
| --- | --- | --- | --- | --- | --- | --- |
| {{monthly_net_income}} | {{monthly_expenses}} | {{monthly_debt_service}} | {{monthly_reserve_contribution}} | {{surplus_before_goals}} | {{declared_goal_contributions}} | {{remaining_after_goals}} |

Show `not-evaluable` or `not-assessed-in-goal-progress-mode` when applicable. Identify each input
source. Do not substitute zeros for missing expense, debt, reserve or income evidence.

## Shared funding ledger

| Pool / account IDs | Balance | Reserved | Assigned across goals | Unassigned | Source IDs |
| --- | --- | --- | --- | --- | --- |
| {{pool_id / account_ids}} | {{balance}} | {{reserved_amount}} | {{assigned_amount}} | {{unassigned_amount}} | {{source_ids}} |

Explain each over-allocation, unknown funding item and its affected goals. Every account appears
once; this table precedes any assessment of individual goal progress.

## Debt and goal discussion

| Debt | Current payment | Payoff months | Modeled total interest | Scope / status | Source IDs |
| --- | --- | --- | --- | --- | --- |
| {{debt_id}} | {{current_month_payment}} | {{payoff_months}} | {{total_interest}} | {{status}} | {{source_ids}} |

| Goal / human priority | Allocated balance | Monthly contribution | Target date / basis | Projected value | Funded ratio | Funding gap | Conditional band |
| --- | --- | --- | --- | --- | --- | --- | --- |
| {{goal_id / priority}} | {{allocated_balance}} | {{monthly_contribution}} | {{target_date / target_basis}} | {{projected_value}} | {{funded_ratio}} | {{gap_at_target_date}} | {{projection_band}} |

For each goal, show source IDs, assumptions version, return/inflation convention, extension months,
continuously inflated extension target and corresponding projected value. A null extension means
no solution found within the stated limit. Additional monthly contribution figures are discussion
illustrations; reconcile proposed changes jointly against the budget before a human selects them.

## Missing evidence and next steps

List every finding with affected goal/pool, source, responsible human and the required evidence.
Distinguish a known funding deficit from missing data. Keep unresolved conflicts visible.

Attach the complete minimized input snapshot, source registry, input hash and model limitations.
No investment selection, debt product recommendation, payment or transfer is authorized here.

## Upstream evidence concerns

Show every `result.upstream_issues` record with its originating artifact, original code/message,
status and source IDs. Include attributed external resolution evidence where supplied. An absent
inventory is unknown, and an unresolved issue prevents review-ready regardless of arithmetic.
