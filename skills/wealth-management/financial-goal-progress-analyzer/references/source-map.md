# Source Map — financial-goal-progress-analyzer

## Source hierarchy (highest first)

| Rank | Source (MCP integration) | Used for | Access |
| ---- | ------------------------ | -------- | ------ |
| 1 | **Planning engine / CRM** goal records | Goal objective, target amount, target date, terms, priority | Read-only |
| 2 | **Portfolio accounting / OMS** (position of record) | Dedicated balance per goal / account | Read-only |
| 3 | **Cash-flow schedule** (plan/CRM) | Recurring contribution amounts | Read-only |
| 4 | **Approved assumptions** (versioned capital-market/planning config) | Expected return, inflation, status thresholds | Read-only |
| 5 | **Product data / disclosures / restrictions** | Context and constraints surfaced for the advisor (not used to decide) | Read-only |

Never substitute a client assertion for the account record. If the goal record, balance, or
contribution schedule conflict across sources, cite both and flag for the advisor.

## Citation format

`{system}:{ref}` — e.g. `portfolio:acct=****4021-IRA;asof=2026-07-15`,
`goals:client=****4021;goal=G-RET`, `assumptions:cma-2026.Q2`. Every goal finding cites the
goal record, the balance, the contribution schedule, and the assumptions version used.

## Freshness / effective dates

- Approved assumptions (returns, inflation, thresholds) are a **versioned contract**; the
  output records the `assumptions_version` so an analysis is reproducible.
- Balances and contributions carry an as-of date; state it and flag staleness.
- Projections use whole months between the as-of date and each goal's target date.

## Least-privilege operations (deployment)

- `goals.read(client_id)` → goal records (target, date, terms, priority).
- `portfolio.balance(account_id|goal_id, as_of)` → dedicated balance rows.
- `cashflow.schedule(client_id|goal_id)` → recurring contribution amounts.
- `assumptions.get(version)` → expected return, inflation, status thresholds.
All read-only, deterministic, durable `analysis_id`, below the fixed timeout; page long goal
sets as resumable stages.
