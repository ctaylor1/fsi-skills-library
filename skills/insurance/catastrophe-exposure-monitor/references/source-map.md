# Source Map — catastrophe-exposure-monitor

## Source hierarchy (highest first)

| Rank | Source (MCP integration) | Used for | Access |
| ---- | ------------------------ | -------- | ------ |
| 1 | **Policy administration** (position of record for exposure) | In-force policies, insured locations, limits, TIV, construction/occupancy, geocodes | Read-only |
| 2 | **Event feed** (peril footprints) | Hurricane tracks/cones, wildfire perimeters, earthquake shakemaps, flood/SCS footprints and their `as_of` | Read-only |
| 3 | **Actuarial / catastrophe model** | Modeled loss (low/mid/high), AAL/PML, damage functions, event severity | Read-only |
| 4 | **Reference / geocode data** | CRESTA-style accumulation zones, geocoding, construction/occupancy taxonomy | Read-only |
| 5 | **Claims** (post-landfall enrichment) | Emerging reported/paid loss for an in-progress event (context only) | Read-only |
| 6 | **Cat-risk config** (versioned) | Zone accumulation limits, single-location max, modeled-loss appetite, staleness limits, severity bands | Read-only |

Producer systems establish policy provenance but are **not** an exposure source of record;
resolve every location back to policy administration. Never substitute a modeled figure for
the position-of-record limit/TIV. If the event feed and the model disagree on footprint,
cite both and flag for the reviewer — do not silently reconcile.

## Citation format

`{system}:{ref}@{as_of}` — e.g. `pas:pas;loc=L-2@2026-07-17T06:00:00`,
`model:nhc;adv=27@2026-07-17T06:00:00`. Every alert cites the specific location rows (or the
event modeled-loss row) behind the breached metric, and the run records the config version.

## Freshness / effective dates

- Each source carries an `as_of`; the monitor computes age vs `max_source_staleness_hours`
  (per-source, with a default). A stale source sets run `confidence: degraded` and is
  reported in `sources[]` — it never silently trusts an old feed.
- Event feeds are the most time-sensitive (default max staleness 6h); models tolerate more
  (48h); policy snapshots 24h. Configure per deployment and per peril.
- The config (thresholds, appetite, bands) is a **versioned contract**; the run records the
  `config_version` so an alert package is reproducible.

## Least-privilege operations (deployment)

- `pas.exposure(as_of)` → bounded, paged in-force locations with limit/TIV/geocode.
- `events.footprints(as_of)` → active/forecast event footprints and severity.
- `model.loss(event_id, location_ids)` → modeled low/mid/high per location.
- `refdata.zone(geo)` → accumulation-zone resolution.
- `config.get('cat', version)` → thresholds + appetite + staleness limits + bands.

All read-only, deterministic, durable `run_id`, below the fixed timeout; page large
portfolios as resumable stages. The monitor never opens a write path.
