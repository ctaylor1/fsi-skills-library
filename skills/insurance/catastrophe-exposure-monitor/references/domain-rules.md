# Catastrophe exposure monitoring rules

These are configurable monitoring conventions, not legal solvency tests or licensed catastrophe-model methodology. The script processes supplied JSON; it does not run a catastrophe model or create a scheduled job.

## Input and financial basis

Use a timezone-aware `as_of`, `config_version`, `exposure_snapshot_id`, context/versioned sources from [insurance-contract.md](insurance-contract.md), `data_coverage` declarations for events/exposures/models, `events[]`, `locations[]`, `prior_alerts[]` and threshold `config`. Missing feeds or coverage are explicit partial/unknown states.

`financial_context` requires currency, `unit: currency`, `financial_basis: gross|net|ceded`, and `limit_grain: location`. Thresholds use that same basis. Each location has unique `location_id`, unique allocated `limit_id`, `zone`, `peril_exposed[]`, finite nonnegative `limit` and `tiv`, boolean `geocoded`, `valuation_date`, `source_ref` and `modeled_losses[]`. Row-level financial overrides must match the run. Shared policy limits require an upstream documented allocation; duplicate limit IDs are excluded and reported so one policy limit is not counted repeatedly. No implicit FX or financial-basis conversion occurs.

Events require `event_id`, `peril`, `footprint_zones[]`, `footprint_version`, `footprint_as_of`, and `source_ref`. Feed references/versions must match the supplied `event_feed` source. `exposure_snapshot_id` must match the `policy_admin` source version.

## Modeled loss binding

Each location model row requires `event_id`, `peril`, `footprint_version`, `exposure_snapshot_id`, `model_version`, `model_run_id`, currency/unit/financial basis, `statistic: scenario_range`, `scenario_set_id`, `scenario_ids: {low,mid,high}` and finite ordered `low <= mid <= high` amounts. Three distinct scenario IDs must identify the same named scenarios across all contributing locations. `model_version`/`model_run_id` match the cat-model source version/reference.

Only fully bound results for every location identified as exposed to that event may form an event model total. The names low/mid/high describe supplied aligned scenarios; they are not marginal percentiles. Different events, perils, footprints, exposure versions, model runs, scenario sets/IDs, currencies, or gross/net bases are not mixed. Marginal quantiles, AAL, PML and return-period estimates are not additively combined by this helper. A source-provided portfolio model result needs a separately defined input method; do not disguise it as a location sum.

## Metrics and bands

Zone accumulation sums unique allocated geocoded location limits; TIV is separate. Single-location metrics use those same limits. Incomplete locations remain explicit data gaps; an observed subtotal is not a full-portfolio loss estimate. A zero-location observation requires a nonempty, complete exposure snapshot with fresh bound source evidence and no location gaps; unavailable or incomplete exposure data produces no numeric zero observation. A complete portfolio entirely outside the footprint can establish zero exposure. Model totals are withheld on incomplete/incompatible event evidence.

For `ratio = metric / threshold`, Critical starts at 1.5 (P1), Elevated at 1.25 (P2), Watch at 1.0 (P3), and Informational at configured `approaching_ratio` (default 0.9, P4). Values below the approaching level produce no new alert. These priorities are review suggestions only. Defaults are illustrative and must be replaced/configured by the risk owner before production use.

## Freshness and prior alerts

The required source roles are policy_admin, event_feed and cat_model. Each has a timestamp, version and reference. Compare age to configured staleness hours. Missing/invalid time is `unknown`; negative age is `future`; excessive age is `stale`. All degrade the run.

New and ongoing breaches retain stable keys. A prior alert is `cleared` only when the same metric is explicitly measured below threshold using complete current evidence. An absent event, deleted location, missing/stale feed, incomplete coverage, incompatible model or unknown metric produces `unknown` and retains the prior alert. An empty snapshot is not an all-clear. Clearing is an observation, never closure of a case or action in a queue.

The output retains every evaluated metric, four dedup counts, source states, gaps, unresolved issues, and a content-bound artifact. `current_evidence` records the current snapshot's completeness and issues before prior-alert reconciliation. An otherwise complete snapshot can support a measured zone clear while a different, unobserved prior metric remains unknown. Every retained unknown alert becomes an unresolved issue and makes the overall run partial with degraded confidence; without an observed breach its overall severity is Unknown. A no-exposure run does not invent a zero modeled-loss result to clear an old model alert. The monitor never writes, binds, settles, buys reinsurance or changes capacity/reserves.
