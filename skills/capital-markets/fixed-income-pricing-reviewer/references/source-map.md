# Source Map — fixed-income-pricing-reviewer

## Source hierarchy (highest first)

| Rank | Source (MCP integration) | Used for | Access |
| ---- | ------------------------ | -------- | ------ |
| 1 | **Independent-pricing / IPV** (vendor consensus, evaluated prices, executable quotes) | The challenge reference the submitted mark is tested against | Read-only |
| 2 | **Market & reference data** (benchmark curves, comparable-bond spreads, ratings, instrument terms) | Spread-to-comparables, corroborating moves, instrument resolution | Read-only |
| 3 | **OMS/EMS marks** (submitted/trader mark, prior mark, applied adjustments, assigned FV level) | The subject under review | Read-only |
| 4 | Valuation-control **config** (versioned thresholds and priority mapping) | Check tolerances and band mapping | Read-only |

The submitted mark is the **subject**, never the authority for its own correctness. Where the
independent price and a broker/dealer quote conflict, cite both and flag for the reviewer; do
not silently pick a "winner". A vendor/independent price can itself be stale or thin — cite its
timestamp rather than treating it as ground truth.

## Citation format

`{system}:{ref}@{date}` — e.g. `mark:oms=BK;instr=INSTR-A@2026-07-15`. Every flagged check cites
the specific instrument/source row and the as-of date; spread checks additionally record the
comparable median and the instrument spread used.

## Freshness / effective dates

- Config (thresholds, band mapping, liquidity bands) is a **versioned contract**; the output
  records the `config_version` used so a review is reproducible.
- The as-of date bounds the review; `price_source_ts` and `last_price_change_date` are compared
  against it for the staleness check.
- Distinguish a stale **vendor feed** (old `price_source_ts`) from a stale **trader mark** (old
  `last_price_change_date`) — they route differently.

## Least-privilege operations (deployment)

- `ipv.price(instrument_id, as_of)` → independent/evaluated price + timestamp + source rank.
- `refdata.comparables(instrument_id)` → comparable spreads, benchmark curve point, terms.
- `oms.mark(instrument_id, as_of)` → submitted mark, prior mark, applied adjustment, FV level.
- `config.get('fi-pricing', version)` → thresholds + liquidity bands + priority mapping.
All read-only, deterministic, durable `review_id`, below the fixed timeout; page a large book
into resumable stages by instrument.
