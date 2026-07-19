# Domain Rules — key-risk-indicator-monitor

How the monitor evaluates each Key Risk Indicator across five lenses and maps results to alert
severity. **Every threshold, direction, and seasonal baseline is versioned configuration**
owned by the risk-appetite function (`config_version`); thresholds are never hard-coded here,
never inferred from observations, and never tuned per-metric. Orientation references: the
firm's risk-appetite statement and KRI standard, the operational-risk / loss-event taxonomy,
and Basel/regulatory metric definitions (e.g., LCR) take precedence over anything in this file.

## Lens taxonomy

| `breach_type` | Scope | Fires (default config) | Evidence attached |
| ------------- | ----- | ---------------------- | ----------------- |
| `threshold` | latest observation | Value crosses the amber band (WARN) or strictly beyond the red band (BREACH), per `direction` | Value, band, amber/red, threshold |
| `trend` | observation history | `trend_min_moves` (default 3) consecutive adverse-direction moves, while **not** already red | From/to values, consecutive moves |
| `seasonal` | latest observation | Adverse deviation from `seasonal_baseline[period]` beyond `seasonal_tolerance_pct` | Value, seasonal expected, bound, deviation % |
| `data_quality` | latest observation | No observations, a null latest value, or a value outside `plausible_range` | Period, value, reason |
| `freshness` | KRI | `observation_as_of` older than `max_staleness_days` | Observation date, staleness, limit |

## Direction and threshold classification (deterministic)

Each KRI declares a `direction`:

- **`higher_is_worse`** (e.g., delinquency rate, failed-payment rate, VaR utilization) — amber
  ≤ red. **BREACH** when `value > red`; **WARN** when `value >= amber` (and ≤ red); else PASS.
- **`lower_is_worse`** (e.g., Liquidity Coverage Ratio, capital ratio) — amber ≥ red. **BREACH**
  when `value < red`; **WARN** when `value <= amber` (and ≥ red); else PASS.

**Boundary convention:** a value exactly on the red limit is an at-limit **WARN**, not a
BREACH — the engine breaches only when strictly beyond red (or strictly under a floor). This
mirrors the library-wide convention and is re-derived identically in
`scripts/calculate_or_transform.py` and `scripts/validate_output.py`.

## Trend, seasonal, and data-quality lenses

- **Trend** is an *early warning*: it fires only while the KRI is **not** already a red BREACH
  (a breach already escalates on its own). It requires `trend_min_moves` consecutive
  observations each moving in the adverse direction, so a single noisy point does not trigger
  it. Insufficient history → the lens is skipped for that KRI.
- **Seasonal** is an *additional lens*: a reading can be within absolute appetite yet far
  outside its seasonal norm. The engine compares the latest value to `seasonal_baseline[period]`
  and raises a BREACH when the adverse deviation exceeds `seasonal_tolerance_pct`. It can
  co-occur with a threshold alert (a different `breach_type` → a different fingerprint).
- **Data quality** protects against a false all-clear: a missing/null latest value or an
  out-of-range value raises a data-quality alert, and the KRI's thresholds are **not** evaluated
  on absent data.

## Position vs. freshness (`stale_input`)

- A KRI whose `observation_as_of` exceeds `max_staleness_days` raises a `freshness` alert, and
  **every** alert derived from that KRI is flagged `stale_input: true`. Results over stale data
  are treated as low-confidence pending a refreshed feed; they are never dropped or presented as
  current.

## Severity mapping (deterministic, documented)

Severity is a triage suggestion, computed from `(breach_type, status, critical)` — see
`expected_severity` in `scripts/calculate_or_transform.py` and re-derived in
`scripts/validate_output.py`:

| Severity | Rule / condition | Routed queue |
| -------- | ---------------- | ------------ |
| **High** | A `threshold` **BREACH** (red band) on a **critical** KRI | `risk-committee-escalation` |
| **Medium** | A `threshold` BREACH on a non-critical KRI, any `seasonal` BREACH, or a `data_quality` alert on a **critical** KRI | `risk-review-queue` |
| **Low** | Any WARN (amber threshold or adverse trend), a `freshness` alert, or a `data_quality` alert on a non-critical KRI | `kri-monitoring-watchlist` |

Severity and queue are fully determined by the lens result and the versioned config; they are
never adjusted by hand for a specific KRI, owner, or business unit.

## Deduplication

Each result has a stable `fingerprint` = `kri_id|breach_type|status`. The run compares
fingerprints to the `open_alerts` baseline: matches are marked `is_duplicate` and routed to
**still-open** (not re-raised as new); everything else is **new**. This keeps a persistent
breach from re-alerting every scheduled run while still recording that it remains open.

## Hard boundaries (fail closed)

- **Alert only.** Never accept a risk, grant/track a waiver, change a limit/threshold/appetite,
  change a risk or control rating, declare an appetite breach, file a report, or close/suppress
  an alert, incident, or case. Those are human risk-governance actions.
- **No threshold invention or tuning.** Use only the versioned config; if a band or direction is
  missing or ambiguous, report the gap rather than guessing a threshold.
- **No intent or advice.** Describe a breach factually (measured vs threshold); do not assert a
  control failure or wrongdoing, nor recommend a specific limit, waiver, or remediation.
- **No silent staleness or missing data.** If an observation is stale or missing, flag it; do
  not present stale results as current or a missing value as a PASS.
