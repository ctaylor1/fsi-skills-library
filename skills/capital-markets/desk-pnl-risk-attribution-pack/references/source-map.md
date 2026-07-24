# Source Map — desk-pnl-risk-attribution-pack

## Source hierarchy (highest first)
| Rank | Source (MCP integration) | Used for | Access |
| ---- | ------------------------ | -------- | ------ |
| 1 | P&L system (system of record) | Reported desk P&L | Read-only |
| 2 | Risk-attribution feeds | Component values (market, carry, fees, new trades, funding) | Read-only |
| 3 | Attribution config (versioned) | Component taxonomy + tolerance | Read-only |
| 4 | Reference data | Desk/book normalization | Read-only |

The P&L system provides the reported figure; the packet never overwrites it. If a component feed
conflicts with the P&L, cite both and flag the residual.

## Citation format
`{system}:{ref}@{as_of}` — e.g. `risk:desk=DESK-4;component=market_pnl@2026-07-18`,
`pnl:desk=DESK-4@2026-07-18`. The residual and each component cite their source.

## Freshness / effective dates
- All figures are **as of** the supplied `as_of`; mixed as-of feeds are flagged.
- Tolerance config is a **versioned contract**; the output records the version.

## Least-privilege operations (deployment)
- `pnl.read(desk_id, as_of)` → reported P&L — read-only, bounded.
- `risk.read_attribution(desk_id, as_of)` → components — read-only.
- `config.get('pnl_attribution', version)` → tolerance — read-only.
Durable `attribution_id`; deterministic; below the fixed timeout; no mutation.
