# Domain Rules — desk-pnl-risk-attribution-pack

The attribution taxonomy and tolerance govern (versioned). Orientation: reported P&L should be
explained by the sum of risk-based components; the unexplained residual is what product control
investigates.

## Computation (deterministic)
| Metric | Definition |
| ------ | ---------- |
| `explained` | Σ component values (signed; fees/funding typically negative) |
| `residual` | `reported_pnl − explained` |
| `abs_residual` | `|residual|` |
| `unexplained_break` | `abs_residual > tolerance_abs` (or bps-of-gross if configured) |
| `contributions` | Components ranked by absolute value, each with signed contribution |

Non-numeric components are excluded and flagged (the residual is then marked incomplete).
Tolerance is a **versioned contract**; it is never invented.

## Disposition mapping (review-only)
- `tied` — residual within tolerance (still reported; small ≠ zero).
- `breaks-for-review` — residual exceeds tolerance. A triage suggestion for product control,
  **not** a sign-off or an instruction to adjust.

## Hard boundaries (fail closed)
- Never adjust/restate/book P&L; never sign off/attest/certify; never approve a break; never
  invent a tolerance; never coerce a non-numeric component.
