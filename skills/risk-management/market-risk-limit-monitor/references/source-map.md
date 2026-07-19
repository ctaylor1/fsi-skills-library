# Source Map — market-risk-limit-monitor

## Source hierarchy (highest first)

| Rank | Source (MCP integration) | Used for | Access |
| ---- | ------------------------ | -------- | ------ |
| 1 | **Limit & risk-appetite register** (versioned) | The definition of record for every limit: VaR, ES, sensitivity, stress-loss, notional, and concentration limits, their `direction`, `warn_buffer_pct`, and `config_version` | Read-only |
| 2 | **Market-risk engine** (risk book of record) | Measured VaR / expected shortfall, sensitivities (DV01/CS01/vega), and scenario stress P&L per book / desk / firm unit | Read-only |
| 3 | **Position / sub-ledger** (front office + risk) | Positions and notional that feed the risk measures; pre-deal / pending exposure for projected checks | Read-only |
| 4 | **Scenario library** (versioned) | Stress-scenario definitions and their computed losses | Read-only |
| 5 | **Market & reference data** | Prices, curves, vols, issuer/desk classification underlying the measures | Read-only |
| 6 | **Prior open-breach register** | Deduplication of already-open limit breaches across runs | Read-only |

The **limit register is the definition of record** for every limit. Never infer a limit from
the measured exposure, a desk head's assertion, or a prior run. The **risk engine is the book
of record for the risk numbers themselves** — this monitor reads VaR/ES/stress values; it
does **not** re-derive or re-aggregate them (VaR is not additive across books, so a
desk/firm number must be provided pre-aggregated as its own unit). If the register and the
risk engine disagree on scope (e.g., which book a limit applies to), cite both and raise the
ambiguity — do not resolve it silently.

## Citation format

`{system}:{ref}@{as_of}` — e.g.
`risk:book=RATES-GOVT;metric=var:1d:0.99@2026-07-17T18:00:00Z`,
`risk:book=FX-EM;measured_as_of=2026-07-16T06:00:00Z@2026-07-17T18:00:00Z`, and each limit
cites `limits:limit_id=VAR-RATES-1D-99@mrl-cfg-2026.07`. Every alert cites the measured
evidence row(s) and the limit (with its config version).

## Freshness / effective dates

- Limits are a **versioned contract** (`config_version`); the pack records the version so a
  run is reproducible and a breach can be tied to the exact limit in force.
- Each unit carries `measured_as_of` (an intraday timestamp). The monitor computes
  `staleness_hours` against the run `as_of` and the framework's `max_staleness_hours`.
  Market-risk numbers are intraday/COB, so freshness is measured in **hours**, not days.
- **Stale data is flagged, never suppressed.** A stale unit raises a freshness alert and
  every alert derived from it is marked `stale_input: true`; results are treated as
  low-confidence pending refreshed measures, not silently dropped.

## Least-privilege operations (deployment)

- `limits.get(framework_id, config_version)` → the versioned limit set.
- `risk.measures(unit_id, as_of)` → VaR / ES / sensitivities / stress P&L for a unit.
- `positions.notional(unit_id, as_of)` → notional / concentration inputs; pending pre-deal
  exposure for projected checks.
- `scenarios.get(scenario_id, config_version)` → stress-scenario definitions.
- `refdata.resolve(security|issuer|curve|desk)` → normalized classifications.
- `breaches.open(framework_id)` → previously-open breach fingerprints for deduplication.

All read-only, deterministic, below the fixed timeout, with a durable `run_id`. Page large
position sets as resumable stages. The monitor writes **nothing** back to any system of
record — it only emits alerts and queue items for human review.
