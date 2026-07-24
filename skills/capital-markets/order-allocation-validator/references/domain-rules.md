# Domain Rules — order-allocation-validator

The firm's approved allocation policy governs (versioned). Orientation: fair-and-equitable
allocation, pro-rata by participation, timely allocation, and documented exceptions.

## Checks (deterministic)
| Check | Rule (default config) | Exception when |
| ----- | --------------------- | -------------- |
| `quantity_tie` | Σ allocated qty == executed qty | Not equal (route as a break) |
| `pro_rata` | Each account's target = executed_qty × participation_weight (method `pro_rata`) or price-time order | \|proposed − target\| > `tolerance_pct` of target (default 0.5%), rounded to `lot_size` |
| `eligibility` | Every allocated account is eligible/entitled for the instrument | Account flagged ineligible/restricted |
| `timestamp` | order_ts ≤ allocation_ts ≤ batch_cutoff (same trade date) | Allocation before fill or after cutoff |
| `deviation_documented` | Any pro-rata deviation carries a documented `deviation_reason` | Deviation present with no reason |

Config (`tolerance_pct`, `lot_size`, `method`, `batch_cutoff`) is a **versioned contract**;
the output records the version. Tolerances are policy, never guessed per order.

## Disposition mapping (review-only)
- `clean` — no exceptions fired.
- `exceptions-for-review` — ≥1 exception. This is a triage suggestion for a human reviewer,
  **not** an allocation decision or a compliance determination.

## Hard boundaries (fail closed)
- Never allocate/re-allocate/amend/book; never override eligibility; never certify compliance;
  never rationalize an undocumented deviation.
- A quantity break is routed to `trade-break-resolver`, not adjusted here.
