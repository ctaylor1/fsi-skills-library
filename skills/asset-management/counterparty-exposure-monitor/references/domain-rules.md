# Domain Rules — counterparty-exposure-monitor

How counterparty exposures are aggregated and how thresholds and credit developments map to
**alert severities** and an **escalation queue**. Limits, floors, and thresholds are
configuration (versioned, owned by the counterparty-risk / compliance limit register), not
hard-coded judgments, and never tuned to an individual counterparty on the fly. The firm's
counterparty-credit-risk (CCR) standard takes precedence over these defaults.

## Exposure aggregation (deterministic)

Per exposure row, **net exposure** is:

```
net_exposure = max(0, current_exposure - collateral) + pfe_addon
```

- `current_exposure` is the positive replacement cost / exposure amount (netting-set-netted
  for derivatives, gross settlement/financing amount otherwise).
- `collateral` (VM/IM held) reduces the current portion, floored at 0.
- `pfe_addon` (potential future exposure) is additive and defaults to 0 when absent.

Per counterparty, **net current exposure** = sum of `net_exposure` across all exposure
types (settlement, derivative MtM, financing/repo, deposit). The book total is the sum
across counterparties. There is no opaque composite "risk score"; every number ties to
cited exposure rows.

## Limit utilization → severity

| Severity | Rule (default config) |
| -------- | --------------------- |
| **Warning** | utilization ≥ `warn_pct` (0.80) and < `breach_pct` |
| **Breach** | utilization ≥ `breach_pct` (1.00) and < `critical_pct` |
| **Critical** | utilization ≥ `critical_pct` (1.10) |

`utilization = net_current_exposure / total_current_exposure_limit`. A counterparty with no
configured limit is reported `not_evaluable` (data gap), never assumed unlimited.

## Single-name concentration → severity

`share_pct = 100 * net_current_exposure / book_total`.

| Severity | Rule |
| -------- | ---- |
| **Warning** | `share_pct` ≥ `concentration_warn_pct` (30.0) and < limit |
| **Breach** | `share_pct` ≥ `single_name_concentration_pct` limit (e.g. 40.0) |

## Credit developments → severity

| Signal | Fires when | Severity |
| ------ | ---------- | -------- |
| `rating_below_floor` | counterparty long-term rating is weaker than its configured `rating_floor` | **Breach** |
| `negative_watch` | rating watch is negative | **Warning** |
| `cds_widening` | `cds_bps - cds_baseline_bps` ≥ `cds_widen_breach_bps` (150) | **Breach** |
| `cds_widening` | widening ≥ `cds_widen_warn_bps` (50) and < breach | **Warning** |

Rating comparison uses a fixed long-term-scale ladder (AAA … D). A rating not on the ladder
is treated as not-evaluable for the floor check, not as a pass.

## Severity → escalation/queue (deterministic packaging)

| Severity | Queue | SLA (human response) | Escalate to |
| -------- | ----- | -------------------- | ----------- |
| **Critical** | `counterparty-risk-urgent` | 1h | Counterparty risk lead and Treasury |
| **Breach** | `counterparty-risk` | 4h | Counterparty risk analyst |
| **Warning** | `counterparty-risk-watch` | 24h | Counterparty risk analyst |

`data_freshness` alerts are severity **Warning** (data-quality) and route to the watch
queue. The SLA is a **human** response target — it never triggers an automated action.

## Deduplication & recurrence

Each alert has a stable `fingerprint`: `{scope}:{counterparty_id}:{alert_type}:{dimension}`
(feed alerts use `feed::data_freshness:{feed}`). Severity changes update the alert in place;
they do not create a new fingerprint. An incoming run compares fingerprints to the prior
`open_alerts` set and marks each `recurring` (already open) or `new`. This keeps the queue
free of duplicate open alerts across scheduled runs.

## Freshness handling

- A feed older than its `max_age_hours` is **stale**.
- A stale feed raises a `data_freshness` alert **and** tags every dependent counterparty
  alert `freshness: stale`. Stale inputs are surfaced, never suppressed or dropped.

## Hard boundaries (fail closed)

- Never post/recall collateral, call margin, change a limit, terminate/novate a trade,
  unwind/hedge, block/suspend a counterparty, or settle/cancel a trade.
- Never make or communicate a binding counterparty/credit/trading decision.
- Never close, resolve, or suppress an alert outside the deterministic dedup logic; never
  drop an exposure because a feed is late.
- Never tune limits/floors/thresholds to a counterparty on the fly; use only the versioned
  config.
