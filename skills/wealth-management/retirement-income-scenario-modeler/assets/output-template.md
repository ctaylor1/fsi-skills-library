# Retirement scenario discussion — {{artifact_id}}

As of {{as_of}} · Capacity {{engagement.capacity}} · USD · Model {{result.model.version}}
Opening balances date {{result.projection.opening_balance_date}} · Modeled ages {{start_age}}–{{end_age}}, inclusive
Human review required · Draft only · Not delivered

## Scenario comparison

| Scenario | Terminal balance | First spending-shortfall age | Total spending shortfall | First asset-depletion age | Depleted before horizon? | Depleted by horizon? |
| --- | --- | --- | --- | --- | --- | --- |
| {{scenario_id}} | {{terminal_portfolio}} | {{first_spending_shortfall_age}} | {{total_spending_shortfall}} | {{first_asset_depletion_age}} | {{assets_depleted_before_horizon}} | {{assets_depleted_by_horizon}} |

A spending shortfall can occur while substantial assets remain under a fixed-percentage withdrawal
policy. Depletion at the final age is by the horizon, not before it. Neither measure is a probability.

## Assumptions, evidence and limits

Show every account opening balance, annual return, effective withdrawal-tax proxy, withdrawal
order, net spending/inflation assumption, source IDs and model version. For every income stream,
show its own first-payment-age dollars, start/end ages, COLA and effective income-tax proxy.
Show all scenario return/inflation adjustments and early return overrides.

Reproduce the complete limitation register: RMDs, tax brackets/capital gains, benefit entitlement,
survivor changes and healthcare/long-term care. State the treatment of each, not just its title.

## Annual results — repeat for each scenario

| Age | Opening portfolio | Net spending | Net income | Gross withdrawals | Withdrawal tax | Net withdrawals | Return | Closing portfolio | Spending shortfall | Surplus excluded from reinvestment |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| {{age}} | {{beginning_portfolio}} | {{net_spending_need}} | {{net_income}} | {{gross_withdrawals}} | {{withdrawal_tax}} | {{net_withdrawals}} | {{investment_return}} | {{ending_portfolio}} | {{spending_shortfall}} | {{surplus_not_reinvested}} |

Attach each annual account/income subledger. Account opening minus gross withdrawals plus return
must equal closing. Income plus net withdrawals plus shortfall must equal spending plus surplus.
Summaries must reconcile to these rows; a claimed tie-out flag is not evidence.

## Gaps and human review

List missing assumptions, unsupported model scope and known scenario shortfalls distinctly.
Do not calculate a missing tax rate, benefit entitlement or income stream by assumption. Preserve
complete independent scenarios when a different scenario lacks evidence. Attach the full source
registry, complete minimized input snapshot, artifact ID and input hash with the standing note.

## Upstream evidence concerns

Show every `result.upstream_issues` record with its originating artifact, original code/message,
status and source IDs. Include attributed external resolution evidence where supplied. An absent
inventory is unknown, and an unresolved issue prevents review-ready regardless of arithmetic.
