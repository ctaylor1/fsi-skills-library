# Domain Rules — catastrophe-exposure-monitor

Deterministic accumulation, threshold, freshness, and deduplication rules and how they map
to a **severity band** and a **suggested response priority**. Thresholds are configuration
(versioned, owned by the cat-risk / actuarial team), not hard-coded judgments, and are never
tuned to a single account or event to make a breach disappear. Orientation references: the
firm's catastrophe risk-appetite standard and the model vendor's event methodology take
precedence.

## Exposure metrics (per event)

An event has a `peril` and a set of `footprint_zones`. A location is **exposed** to the
event when its `zone` is in the footprint AND the event `peril` is in its `peril_exposed`
list. Only **geocoded** exposed locations enter accumulation and modeled-loss aggregation;
ungeocoded exposed locations are reported as data gaps, not silently dropped.

| Metric | Definition | Threshold (versioned config) |
| ------ | ---------- | ---------------------------- |
| `zone_accumulation` | Aggregate exposed **limit** across geocoded locations in a footprint zone (TIV reported alongside) | `zone_accum_limit[zone]` (per-zone, else `default`) |
| `single_location` | A single exposed location's **limit** | `single_location_max` |
| `modeled_loss` | Event **tail** (high) modeled loss = sum of exposed geocoded `modeled_loss.high`; low/mid/high all reported | `modeled_loss_appetite` |

## Severity banding (deterministic)

Each breach carries an `exceedance_ratio = metric / threshold`. The band is a pure function
of that ratio (identical logic in `scripts/calculate_or_transform.py` and
`scripts/validate_output.py`):

| Band | Rule (ratio `r`) | Suggested priority |
| ---- | ---------------- | ------------------ |
| **Critical** | `r >= 1.5` | P1 |
| **Elevated** | `1.25 <= r < 1.5` | P2 |
| **Watch** | `1.0 <= r < 1.25` | P3 |
| **Informational** | `approaching_ratio <= r < 1.0` (default 0.9; early warning, not a breach) | P4 |
| _(no alert)_ | `r < approaching_ratio` | — |

`suggested_response_priority` sets human triage urgency in the queue. It is a triage
suggestion, **not** an underwriting, reinsurance, or reserving decision, and it never
triggers an action.

## Freshness rules

Each source's age = run `as_of` − source `as_of`, compared to
`max_source_staleness_hours[source]` (per-source, else `default`). A source with no `as_of`
or age over its limit is **stale**. Any stale source sets run `confidence: degraded`; the
alert package still lists breaches but flags reduced confidence. A stale **event feed** is
the most material — do not treat an old footprint as current.

## Deduplication rules

Each breach has a stable `alert_key = event_id:zone:peril:breach_type[:location_id]`.
Against the prior run's `prior_alerts`:

- key present last run and still breaching → **ongoing** (carried, not re-raised as new);
- key breaching for the first time → **new**;
- key present last run but not breaching now → **cleared** (metric fell below threshold or
  exposure was removed). Cleared is **not** a disposition or closure.

The `dedup` summary (`new` / `ongoing` / `cleared` counts) must tie to the alerts.

## Data-gap handling (surfaced, never silent)

| Gap | Trigger | Effect |
| --- | ------- | ------ |
| `ungeocoded_excluded` | Exposed location with `geocoded: false` | Excluded from accumulation; reported |
| `stale_valuation` | `valuation_date` older than `stale_valuation_years` (default 3) | Reported; TIV may understate exposure |
| `unmodeled` | Geocoded exposed location with no `modeled_loss` | Excluded from modeled-loss range; reported |

## Hard boundaries (fail closed)

- Never bind/decline coverage, change limits or capacity, buy/cede reinsurance, book/adjust
  reserves, issue/cancel endorsements, or non-renew — describe the exposure and route to the
  human queue and the named downstream skills.
- Never close, suppress, or snooze an alert outside the dedup rule above.
- Never tune a threshold, appetite, or footprint inside a run; those are versioned config
  changes owned by the cat-risk / actuarial team.
- Never present accumulation or modeled loss as certain; always carry the range and the
  confidence flag.
