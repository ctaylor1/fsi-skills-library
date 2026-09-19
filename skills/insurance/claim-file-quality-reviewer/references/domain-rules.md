# Domain rules — Claim File Quality Review

- Select the latest outstanding reserve stock on/before as_of for each balance_id. Historical stocks are not summed. Reserve movements or unspecified semantics are unevaluable.
- Paid total sums uniquely identified nonnegative payment transactions in the declared currency. Duplicate IDs, mixed currencies, future entries, incomplete collections and unsupported reversals/recoveries make financial totals unknown.
- Descriptive incurred = selected outstanding reserve stock + cumulative gross paid transactions. It is neither case-reserve adequacy nor ultimate-loss estimation. Reversals, refunds, net recoveries and reserve-movement ledgers need prior explicit reconciliation.
- Unknown financials emit null totals, Unknown descriptive severity and blocking quality findings, never zero balances. Required-doc presence ignores records marked missing.
- Policy-period checks and missing coverage citations surface review questions. Comparing an indemnity reserve to a supplied support estimate is a traceability exception, not an adequacy opinion.
- Any blocking finding yields escalate; otherwise warnings yield follow_up_required; otherwise documentation_complete. This band describes bounded file checks only.

## Scope limit
File quality and descriptive gross financial reconciliation only. No bulk reserving, recovery accounting, adequacy recommendation, coverage interpretation or approval.
