# Domain Rules — market-risk-limit-monitor

How the monitor evaluates VaR, expected-shortfall, sensitivity, stress-loss, notional, and
concentration limits and maps results to alert severity. **Every limit is versioned
configuration** owned by the market-risk / risk-appetite function (`config_version`); limits
are never hard-coded here, never inferred from the measured exposure, and never tuned
per-book. Orientation references: the firm's market-risk policy and risk-appetite statement,
desk limit mandates, and applicable capital rules (e.g., FRTB / IMA and the Basel market-risk
framework) take precedence over anything in this file.

## Metric taxonomy

| `metric` | Scope | Measured value vs limit | Evidence attached |
| -------- | ----- | ----------------------- | ----------------- |
| `var` | book / desk / firm unit | 1-day (or n-day) Value-at-Risk at a confidence vs `limit_value` | measured VaR, utilization %, limit |
| `es` | unit | Expected shortfall (CVaR) at a confidence vs `limit_value` | measured ES, utilization %, limit |
| `sensitivity` | unit | A Greek (`dv01` / `cs01` / `vega` / `delta`) vs `limit_value` | measured sensitivity, utilization %, limit |
| `stress_loss` | unit | Loss under a named `scenario_id` vs `limit_value` | measured stress loss, scenario, limit |
| `notional` | unit | Gross / net notional or position size vs `limit_value` | notional, utilization %, limit |
| `concentration` | unit (`sub_scope` issuer/sector/curve) | Largest bucket as a % vs `limit_value` (%) | bucket %, utilization %, limit |

A limit joins to exactly the measured unit whose `unit_type`/`unit_id` equals the limit's
`scope`/`scope_value`, and to the measure on that unit matching the metric discriminators
(horizon+confidence for VaR/ES, `sensitivity` for Greeks, `scenario_id` for stress). If no
matching measure exists, the limit is **not evaluable** this run — `validate_input` warns and
the engine emits no alert (it never assumes PASS silently).

## Threshold classification (deterministic)

`utilization_pct = measured / limit_value * 100`. For a `max` limit:

- **BREACH** when `measured > limit_value` (utilization strictly over 100%).
- **WARN** when within `warn_buffer_pct` of the limit but not over — i.e. utilization in
  `[100 - warn_buffer_pct, 100]` (the amber **warning line** / soft limit).
- **PASS** otherwise (no alert emitted).

`min` limits (e.g., a minimum hedge ratio) invert the comparison. A measure exactly **at** the
limit (utilization = 100%, `measured == limit_value`) is **WARN, not BREACH** — the engine
breaches only when strictly over (or under, for floors).

## Current vs. pre-deal (`breach_type`)

- `current` — the **latest measured** risk number for the unit already breaches (or warns on)
  the limit. This is the headline utilization the reviewer sees.
- `projected` — a **pending / pre-deal** exposure (`projected_value` provided by the risk
  engine's what-if) would **newly** cause a BREACH on a limit that is not already breached.
  This is the active pre-deal signal worth catching before the trade is worked. The monitor
  flags it; it never blocks, cancels, or releases the trade.
- `freshness` — the unit's measures are older than `max_staleness_hours`; raised so the
  reviewer knows results may not reflect current risk.

## Severity mapping (deterministic, documented)

Severity is a triage suggestion, computed from `(metric, status, breach_type)` — see
`expected_severity` in `scripts/calculate_or_transform.py` and re-derived in
`scripts/validate_output.py`:

| Severity | Metric / condition | Routed queue |
| -------- | ------------------ | ------------ |
| **High** | Any `var` / `es` / `stress_loss` BREACH, **or** any `projected` (pre-deal) BREACH | `market-risk-escalation` |
| **Medium** | `sensitivity` / `notional` / `concentration` **current** BREACH | `market-risk-review-queue` |
| **Low** | Any WARN (near a warning line), **or** a `freshness` flag | `risk-monitoring-watchlist` |

Severity and queue are fully determined by the limit set and the versioned thresholds; they
are never adjusted by hand for a specific book or desk. Escalation packaging carries an
indicative **SLA** per bucket (same-day / next-business-day / next-run) as a triage aid — a
human owns the clock and the disposition.

## Deduplication

Each result has a stable `fingerprint` = `unit_id|limit_id|bucket|breach_type|status`. The
run compares fingerprints to the `open_alerts` baseline: matches are marked `is_duplicate`
and routed to **still-open** (not re-raised as new); everything else is **new**. This keeps a
persistent breach from re-alerting every scheduled run while still recording that it remains
open. With no baseline, deduplication is disabled and every breach is reported as new (and
`validate_input` warns).

## Hard boundaries (fail closed)

- **Alert only (R3).** Never trade, hedge, cut, trim, or rebalance a position; never grant,
  raise, reset, or waive a limit or temporary excess; never clear, cure, or close a breach;
  never close/suppress/downgrade an alert; never file or submit a breach or regulatory
  report. Those are human risk-management decisions with mandatory adjudication.
- **No limit invention or tuning.** Use only the versioned config; if a limit is missing or
  ambiguous, report the gap rather than guessing a threshold.
- **No re-derivation of risk numbers.** Read VaR/ES/stress from the risk engine; do not
  recompute or sum them across books (VaR is not additive) — a desk/firm limit needs a
  pre-aggregated unit.
- **No intent or advice.** Describe a breach factually (measured vs limit, utilization); do
  not assert wrongdoing, nor recommend a specific trade, hedge, or position change to cure it.
- **No silent staleness.** If measures are stale, flag it; do not present stale results as
  current or drop the unit.
