# Controls — pricing-hedging-scenario-calculator

- **Risk tier:** R3 — regulated/control decision support. **Action mode:** Draft-only; no
  system-of-record change.
- **Human approval:** `required` — for any firm price/quote or execution/hedge placement.

## Prohibited (fail closed)
- No **firm price, quote, bid, or offer**.
- No **executing, putting on, or instructing** a trade or hedge.
- No **assumed risk figure** for a missing parameter; no dividing by a zero hedge DV01.
- No presenting a **linear estimate as exact** for a convex/optioned position.

## Required output screen (`scripts/validate_output.py`)
- Per scenario: `pnl == sign(direction) × position_dv01 × shock_bp` (within tolerance).
- Hedge sizing: `hedge_units × hedge_dv01_per_unit == position_dv01` (within tolerance).
- No firm-price/execution language (regex: firm price/we quote/execute the hedge/put on the
  trade/we filled/lifted the offer/hit the bid/price it firm).
- Standing disclaimer present.

## Segregation of duties
The scenario analyst is not the pricing/execution desk; the worksheet supports, never replaces,
desk pricing and execution.

## Data classification, privacy, records
- **Highly Confidential (customer NPI/PII).** Retain worksheet + parameters.
- Log read + external-delivery approval; enforce information barriers.

## Reproducibility
`scenario_id` binds output to the exact parameters and as_of; computation is deterministic,
linear, and stdlib-only.
