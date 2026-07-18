# Controls — catastrophe-exposure-monitor

- **Risk tier:** R2 — analytical. **Action mode:** Scheduled read-only; alert only.
- **Scheduled agent:** `read-only-monitoring` (one of the approved read-only monitors).
- **Human approval:** `external-delivery` — required before the alert package is distributed
  outside the review queue or written to a system of record. No approval is needed for the
  monitor's own read + queue.

## Scheduled read-only, alert-only posture (defining control)

This skill runs on a schedule, reads its sources, and **raises alerts / queue items**. On
every run it may only:

- **enrich** (resolve zones, join modeled loss to exposed locations),
- **threshold** (compare accumulations / single-location / modeled loss to versioned config),
- **deduplicate** (mark alerts new / ongoing / cleared vs the prior run),
- **queue** (package alerts for the catastrophe-risk review queue).

It must **never act, decide, or close**. Specifically it never binds or declines coverage,
changes limits or capacity, buys or cedes reinsurance, books or adjusts reserves, issues or
cancels endorsements, non-renews a policy, closes or suppresses an alert outside the
deterministic dedup logic, or writes any system of record. Clearing an alert means the
metric fell below threshold this run — it is **not** a disposition or a closure.

## Prohibited (fail closed)

- Any **underwriting / capacity / reinsurance / reserving decision or action**, or a
  recommendation phrased as an instruction to act.
- **Closing, suppressing, or snoozing** an alert outside the documented dedup rule.
- **Threshold tuning to a single account or event** to make a breach disappear; only the
  versioned config is used.
- Presenting modeled loss or accumulation as **certain** — figures are estimates with a
  low/mid/high range and a confidence flag.
- Any **write** to policy admin, the model, or a downstream system.

## Required output screens (`scripts/validate_output.py`)

- **Freshness:** every source has a `fresh|stale` status; any stale source forces
  `confidence: degraded`.
- **Deduplication:** every alert has a stable `alert_key` and a status in
  `{new, ongoing, cleared}`; no duplicate keys; the `dedup` summary ties to the alerts.
- **Escalation / queue packaging:** every active alert has a queue target, ≥1 cited evidence
  row, and a `severity` + `suggested_response_priority` equal to the deterministic mapping
  from its `exceedance_ratio`.
- **No autonomous action:** regex screen for bind/decline/cede/cancel/endorse/reserve/
  limit-change/alert-closure language; the standing disclaimer must be present.

## Escalation latency

Severity band drives the suggested queue priority (Critical→P1 … Informational→P4). The
suggestion sets human triage urgency; it never triggers an action. Escalation-latency SLOs
(time from breach to queued alert) are an operational telemetry target, not a monitor action.

## Data classification, privacy, records

- **Highly Confidential (customer NPI/PII).** Mask policyholder identifiers; carry only the
  location/policy references needed to evidence a breach.
- Retain the run package + citations + config version per records policy; log each read and
  any external-delivery approval. Never exfiltrate portfolio or location data.

## Reproducibility

`run_id` binds the package to the exact snapshot, event footprints, and **config version**;
re-running the same snapshot and config reproduces the alerts, bands, and dedup result.
