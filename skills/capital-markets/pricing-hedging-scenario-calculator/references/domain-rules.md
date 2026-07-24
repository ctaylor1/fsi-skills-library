# Domain Rules — pricing-hedging-scenario-calculator

Orientation: a first-order (linear, DV01-based) scenario and hedge-sizing estimate for a
structuring analyst. Estimate only — never a firm price or an execution.

## Computation (deterministic, linear)
| Metric | Definition |
| ------ | ---------- |
| `sign` | `-1` if direction is `long` (loses as yields rise), `+1` if `short` |
| scenario `pnl` | `sign × position_dv01 × shock_bp` |
| `hedge_units` | `position_dv01 / hedge_dv01_per_unit` |
| `hedge_side` | `short` if the position is `long`, else `long` |
| `residual_dv01` | `position_dv01 − hedge_units × hedge_dv01_per_unit` (≈ 0) |

`position_dv01` is the dollar P&L change per 1bp move. A zero `hedge_dv01_per_unit` makes hedge
sizing not-computable (never divide).

## Limits (must be stated)
- The P&L is **linear/first-order**; large shocks and convex/optioned instruments require full
  revaluation. Never present the linear number as exact for such positions.

## Hard boundaries (fail closed)
- Never state a firm price/quote/bid/offer; never execute/put on/instruct a trade or hedge; never
  assume a missing risk parameter; never divide by a zero hedge DV01.
