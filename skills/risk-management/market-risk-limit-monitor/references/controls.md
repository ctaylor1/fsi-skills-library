# Controls — market-risk-limit-monitor

- **Risk tier:** R3 — regulated / control decision support. **Action mode:** Scheduled
  read-only; alert only.
- **Scheduled agent:** `read-only-monitoring` — runs on a schedule, reads sources, and raises
  alerts / queue items. It **never acts, decides, closes, files, or writes.**
- **Human approval:** `required` — R3 mandates human risk-management adjudication before any
  regulated decision, disposition, limit change, waiver, breach/regulatory filing, external
  delivery, or system-of-record change. The scheduled read and the internal queue are the
  monitor's only outputs.

## Scheduled read-only, alert-only posture (archetype control)

This monitor may **enrich, threshold, deduplicate, and queue**. It may **never**:

- trade, hedge, cut, trim, rebalance, or exit a position or the book;
- grant, raise, reset, extend, or waive a limit or a temporary limit excess;
- clear, cure, or close a limit breach on its own authority;
- close, suppress, snooze, or downgrade an alert on its own authority;
- file, submit, or transmit a breach report or regulatory notification;
- write back to the risk engine, the limit register, the position ledger, or any book of
  record.

Every scheduled run is idempotent for a given `(run_id, config_version, as_of, measures)`:
re-running reproduces the same alerts, severities, and fingerprints. The agent assumes no
automatic retries and no step-up authorization.

## Prohibited (fail closed)

- No **risk decision or disposition** (e.g., "this breach is acceptable", "no escalation
  needed"); describe measured value vs limit and utilization factually.
- No **remediation instruction** — no specific trade, hedge, sizing, or position change to
  cure a breach (that is trading/investment advice and a desk decision).
- No **limit invention, tuning, or change**; only the versioned config is authoritative, and
  changing a limit is a governance action outside this monitor.
- No **re-derivation or cross-book aggregation** of VaR/ES/stress numbers; read them from the
  risk engine as the book of record.
- No **suppression of stale data** — stale measures are flagged, not dropped or presented as
  current.
- No **autonomous alert closure or de-duplication into silence** beyond the deterministic
  fingerprint logic (still-open items remain visible as open).

## Required output screens (`scripts/validate_output.py`)

- Every alert is well-formed: identity, ≥1 cited evidence row (measure + limit), `status` in
  {WARN, BREACH}, a `severity`, and a routing `queue`; threshold-metric alerts carry
  `measured` and `limit`.
- `severity` ties out to the deterministic `(metric, status, breach_type)` mapping and `queue`
  ties out to `severity`.
- Deduplication integrity: `new_alerts` and `still_open` partition alerts by fingerprint;
  duplicates route to still-open and are not re-raised as new.
- Freshness handling: every stale unit has a freshness alert and its alerts are flagged
  `stale_input` — stale data is never silently treated as current.
- **No autonomous-action / decision / closure / filing language** (regex screen: "hedged the
  book", "limit was raised", "granted a waiver", "cleared the breach", "auto-closed", "closed
  the alert", "reported the breach to", "override the limit", etc.).
- Standing disclaimer present (the alert-only disclaimer text).
- Escalation packaging ties out: escalation counts sum to the alert count.

## Data classification, privacy, records

- **Confidential.** Desk positions, risk numbers, and limit utilization are commercially
  sensitive; minimize to what evidences an alert.
- Retain each run's alerts + citations + `config_version` per records policy; log the read,
  the queue emission, and any required human adjudication / external-delivery approval.
- Never exfiltrate positions, risk numbers, or trade intentions; route alerts only to approved
  market-risk queues.

## Reproducibility

`run_id` binds the pack to the exact inputs, measures `as_of`, and **limit config version**;
re-running with the same inputs and config reproduces the alerts, severities, and
fingerprints. Freshness, precision/recall, threshold behavior, deduplication, escalation
latency, and no-autonomous-action are the primary validation targets for this archetype.
