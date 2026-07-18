# Controls — investment-thesis-monitor

- **Risk tier:** R2 — analytical. **Action mode:** Scheduled read-only; alert only.
- **Scheduled agent:** `read-only-monitoring` — runs on a schedule, reads sources, thresholds,
  deduplicates, and stages a review queue. It **never acts, decides, or closes.**
- **Human approval:** `external-delivery` — required before the alert queue is delivered
  externally (emailed to the desk) or written to a system of record. No approval is needed for
  the covering analyst's own read of the staged queue.

## Scheduled read-only, alert-only posture (the defining control)

This monitor is one of the approved read-only scheduled agents. Per every run:

- It **only** reads, enriches, thresholds, deduplicates, and queues. `action_taken` is always
  `none`.
- It raises **alerts and a queue** for a human; it does not resolve, suppress outside the
  documented dedup logic, or take any position/thesis action.
- It cannot trade, rebalance, trim, add, exit, hedge, or **close/retire a thesis**; it cannot
  edit the thesis register, PMS/OMS, or research system of record.
- It cannot provide personalized investment advice.

## Prohibited (fail closed)

- No **investment decision** or recommendation to act: buy, sell, hold, trim, add, exit,
  increase/reduce weight, hedge, liquidate, or rebalance.
- No **thesis close/retire** or change to the documented thesis — the monitor evidences,
  the human decides.
- No **trade/order placement or staging**, and no system-of-record write.
- No **personalized investment advice** ("you should buy/sell").
- No **firing on stale evidence**, and no **tolerance tuning** to force/suppress an alert.
- No **opaque score** presented as decisive; signals are explainable and evidenced.

## Required output screens (`scripts/validate_output.py`)

- `action_taken == "none"` and a durable `monitor_run_id` present.
- Every fired signal has ≥1 cited evidence row, and every fired evidence row is **fresh**
  (age ≤ `max_staleness_days`); each alert carries a `data_freshness` block.
- Suggested escalation equals the deterministic mapping from each alert's fired-challenging set.
- **Deduplication applied:** each alert has a boolean `duplicate`; `queue.new` /
  `queue.deduplicated` partition the alert keys with no overlap; duplicates route to
  `deduplicated`, new to `new`; every key appears under its band in `queue.by_escalation`.
- **No autonomous-action / advice language** (regex screen: "sell the position", "trim the
  position", "exit the trade", "rebalance", "close the thesis", "you should buy/sell", etc.).
- Standing disclaimer present: "Monitoring alert only; not investment advice or a trading
  decision. No position or thesis action has been taken."

## Precision / recall & escalation latency

- Tune tolerances via the **versioned config** to balance false positives (alert fatigue)
  against false negatives (missed thesis breaks) — never per name to force an outcome.
- Deduplication keeps escalation latency measured from the first raise; a continuation is not
  re-escalated.

## Data classification, privacy, records

- **Highly Confidential (MNPI / client-confidential).** A thesis and its evidence may contain
  material non-public information; restrict the queue to entitled research/PM users and handle
  under the firm's information-barrier policy.
- Minimize data in the alert to what evidences a fired signal.
- Retain the run + citations + `config_version` per records policy; log the read and any
  `external-delivery` approval. Never exfiltrate thesis or position data.

## Reproducibility

`monitor_run_id` binds the output to the exact inputs, `as_of`, and **config version**;
re-running the same snapshot with the same config reproduces the signals, bands, and queue.
