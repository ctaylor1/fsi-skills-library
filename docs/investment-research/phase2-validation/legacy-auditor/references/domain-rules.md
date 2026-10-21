# Domain Rules — model-roll-forward-auditor

## Version 0.2.0 contract

Retained through Phase 1 until shared-check and future reviewer parity is established. This is a supplied-balance continuity checker only: it does not read/update a workbook, compare formulas, assess assumptions or provide independent assurance. Require unique line items, model version IDs, explicit balances (null means structural break) and nonnegative explicit tolerances. A tied subset does not establish model correctness.


Orientation: verify that a rolled model carries prior-period ending balances into current-period
opening balances. Continuity only — never valuation or approval.

## Computation (deterministic)
| Metric | Definition |
| ------ | ---------- |
| `residual` | `current_opening − prior_ending` |
| `within_tolerance` | `|residual| ≤ tolerance` (explicit nonnegative tolerance is required) |
| `tie_status` | `tied` if within tolerance, else `break` |
| structural break | An item present in only one version (opening or ending missing) |

Tolerances are documented inputs; a missing tolerance means **exact match**, stated explicitly.

## Disposition mapping (review-only)
- `tied` — every item within tolerance and no structural breaks.
- `breaks-for-review` — ≥1 numeric or structural break. A triage suggestion for the analyst,
  **not** a model sign-off.

## Hard boundaries (fail closed)
- Never opine on valuation/fair value; never approve/validate the model or confirm correctness;
  never assume continuity for a missing balance; never invent a tolerance.
