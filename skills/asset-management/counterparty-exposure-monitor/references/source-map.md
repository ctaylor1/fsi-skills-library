# Source Map — counterparty-exposure-monitor

## Source hierarchy (highest first)

| Rank | Source (MCP integration) | Used for | Access |
| ---- | ------------------------ | -------- | ------ |
| 1 | **PMS/OMS positions & settlement** (position of record) | Settlement, financing/repo, and deposit exposures per counterparty | Read-only |
| 2 | **Derivatives / risk system** | Netting-set MtM, PFE add-ons, collateral (VM/IM) held and posted | Read-only |
| 3 | **Market & credit data** | Ratings, rating watch, CDS levels and baselines; reference prices | Read-only |
| 4 | **Counterparty & entity reference** | Legal entity / netting-set resolution, ownership, parent linkage | Read-only |
| 5 | **Compliance / limit register** (versioned) | Counterparty limits, concentration limits, rating floors, thresholds | Read-only |

Positions and settlement in the PMS/OMS are the record; the risk system supplies MtM,
PFE, and collateral. If a market-data rating and the limit register's rating floor
conflict on scale, cite both and flag for the reviewer — never reconcile silently.

## Citation format

`{feed}:{source_ref}@{feed_as_of}` — e.g. `derivatives_mtm:cp=CP-ACME;set=NS-01@2026-07-17T06:00:00`.
Every alert cites the specific exposure rows (or credit record / feed record) behind it,
each with the feed and its effective timestamp.

## Freshness / effective dates

- Each feed carries an `as_of` and a `max_age_hours`. The monitor computes feed age at run
  time; a feed older than its threshold is **stale**.
- Stale feeds are **surfaced, never suppressed**: a `data_freshness` alert is raised for the
  feed, and every counterparty alert derived from a stale feed is tagged `freshness: stale`
  so the reviewer weighs it accordingly. The monitor does not drop an exposure because its
  feed is late.
- The **config/limit register** (limits, floors, thresholds) is a versioned contract; the
  run records `config_version` so an alert set is reproducible.

## Least-privilege operations (deployment)

- `positions.read(as_of)` → settlement/financing/deposit exposures (bounded, paged).
- `risk.read(as_of)` → netting-set MtM, PFE add-ons, collateral held/posted.
- `marketdata.credit(counterparty_ids)` → rating, watch, CDS level + baseline.
- `refdata.resolve(counterparty|netting_set)` → normalized legal-entity linkage.
- `limits.get('counterparty', version)` → limits, concentration limit, rating floors,
  thresholds.
- `queue.enqueue(alert)` → append-only write to the **human review queue** (the only write;
  it queues an alert for a person — it never mutates positions, limits, or collateral).

All reads are read-only, deterministic, run under a durable `run_id`, and stay below the
fixed timeout; page long exposure books as resumable stages. The monitor performs no
position, limit, collateral, or trade write.
