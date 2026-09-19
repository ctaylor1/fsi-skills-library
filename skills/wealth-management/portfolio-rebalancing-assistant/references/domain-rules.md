# Transition planning economics and limits

Pre-transition NAV = settled cash + sum(position quantity × sourced quote). Reconcile to supplied
position values and portfolio total. Reconcile lot quantities to each position and lot basis to
reported position basis when supplied. Do not infer missing taxable lots from position-level averages.

Generate mode uses the explicit transaction-cost reserve: desired quantity = floor(((preNAV-reserve)
× target weight / quote) / quantity increment) × increment. Differences from current quantities become
sell/buy drafts; this supports exits and new target names. Sells are listed first. This is an explicit
snapshot sizing convention, not a tax or investment recommendation. The reserve is not an assumed fee.
Validate mode evaluates the actual supplied transitions; it never invents trades to repair them.

Fee = trade notional × supplied fee bps/10000 + supplied fixed fee, charged per trade. Verify stated
fees and the reserve. Post cash = starting cash + sale proceeds - purchases - calculated fees.
Post NAV = preNAV - fees, and projected security values plus cash must tie to that NAV. Economic
checks use cumulative security/lot consumption, not each sell independently. No short position is allowed.

Oldest-first is an explicitly chosen deterministic lot convention: acquisition date then lot ID;
specified mode consumes the supplied choices. Allocated basis = lot total basis × sold fraction.
Gross lot gain/loss = sold quantity × quote - allocated basis. Report signed losses as well as gains;
fees are reported separately, with no tax deduction/term-rate conclusion. A supplied tax identity group
can flag same-plan loss/rebuy overlap, but cannot establish complete cross-account, substantially
identical, lookback/forward-window, corporate-action or jurisdictional tax treatment.

Settlement ledger groups credits/debits by explicitly supplied settlement date. Same-day-netting
checks net cash at each date; prefund-buys additionally requires cash before that date's sale credits.
A final funded balance never cures an earlier date's cash deficit. No trade fills or settlement
availability are guaranteed. Dates are supplied scenarios, not inferred venue settlement rules.

Check order notional, total sells/preNAV turnover, explicit restrictions, minimum cash, post-NAV
position weights and target drift including cash. Unknown permissions, conflicting totals, overdrawn
cash, excessive quantities and unresolved limits keep needs-data. Blocked draft lines stay visible
for diagnosis; no output line authorizes submission. A zero-trade result can be valid if already in band.

The complete input hash covers account, mandate/limits, target, sources, assumptions and all proposed
trades. It is not a permission token. No caller role/approval string enables execution. Numerical
reconciliation uses1e-8 for quantities/weights and0.01 currency units for external totals; these are
software tolerances, not trading authority or legal rules. No live order, idempotent execution,
fill verification, tax clearance or guaranteed reversal is implemented.
