# Bounded domain methods

## journal_trial_balance

Require balanced opening signed-debit trial balance and each balanced journal, then roll movements into account closing balances. Credits are negative balances; each journal line has exactly one positive debit or credit.

## accrual

Straight-line ACT/365 expense accrual = principal times annual decimal rate times actual days excluding start /365. No compounding, amortization or day-count selection.

## nav_workpaper

Common net assets = supplied assets minus common liabilities. Allocate by supplied weights summing exactly1, then subtract separate class expenses. Reconcile summed class NAV against a supplied external accounting-engine result; calculate indicative NAV/share.

## Interpretation and exclusions

A supplied external benchmark is mandatory for NAV mode and remains unverified source evidence. No journal-to-valuation or class-flow equalization engine, FX, fair-value policy, tax or authoritative strike/post.

Journal/cash sums and class allocation products use exact Decimal arithmetic. ACT/365 accruals and NAV/share ratios round to8 decimal places, distinct from booked minor-unit rounding.

Use the supplied approved method and policy version; this package does not infer professional approval from source strings. Effective/expiry dates are enforced for referenced sources. Unknown evidence stays unavailable or rejects the input. Multiple modes are separate workpapers; do not add their outputs as if they were independent contributions.
