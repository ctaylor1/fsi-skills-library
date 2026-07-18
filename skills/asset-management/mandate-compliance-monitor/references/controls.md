# Controls — mandate-compliance-monitor

- **Risk tier:** R2 — analytical. **Action mode:** Scheduled read-only; alert only.
- **Scheduled agent:** `read-only-monitoring` — runs on a schedule, reads sources, and
  raises alerts / queue items. It **never acts, decides, closes, or writes.**
- **Human approval:** `external-delivery` — required before an alert pack is delivered
  outside the compliance function or written to a case/system of record. The scheduled read
  and the internal queue are the monitor's only outputs; disposition is human.

## Scheduled read-only, alert-only posture (archetype control)

This monitor may **enrich, threshold, deduplicate, and queue**. It may **never**:

- block, cancel, hold, or release a trade or order;
- buy, sell, rebalance, trim, or exit a position;
- grant, extend, track, or close a cure period or a limit waiver;
- close, suppress, snooze, or downgrade an alert on its own authority;
- write back to the PMS/OMS, the rule library, or any book of record.

Every scheduled run is idempotent for a given `(run_id, config_version, as_of, positions)`:
re-running reproduces the same alerts, severities, and fingerprints. The agent assumes no
automatic retries and no step-up authorization.

## Prohibited (fail closed)

- No **compliance determination** (e.g., "this is a wilful breach") or statement of intent;
  describe measured value vs limit factually.
- No **remediation instruction** — no specific trade, security, sizing, or allocation to
  cure a breach (that is investment advice and a portfolio-management decision).
- No **limit invention or per-portfolio tuning**; only the versioned config is authoritative.
- No **suppression of stale data** — stale positions are flagged, not dropped or presented
  as current.
- No **autonomous alert closure or de-duplication into silence** beyond the deterministic
  fingerprint logic (still-open items remain visible as open).

## Required output screens (`scripts/validate_output.py`)

- Every alert is well-formed: identity, ≥1 cited evidence row, `status` in {WARN, BREACH},
  a `severity`, and a routing `queue`; threshold alerts carry `measured_pct` and `limit`.
- `severity` ties out to the deterministic `(rule_type, status, breach_type)` mapping and
  `queue` ties out to `severity`.
- Deduplication integrity: `new_alerts` and `still_open` partition alerts by fingerprint;
  duplicates route to still-open and are not re-raised as new.
- Freshness handling: every stale portfolio has a freshness alert and its alerts are flagged
  `stale_input` — stale data is never silently treated as fresh.
- **No autonomous-action / decision language** (regex screen: "trade was blocked",
  "rebalanced", "liquidate", "waiver granted", "cured the breach", "auto-closed",
  "closed the alert", "override the limit", etc.).
- Standing disclaimer present: "Monitoring alert only; no trade, block, waiver, cure, or
  system-of-record change has been made. Mandate exceptions require human compliance review
  and disposition."
- Escalation packaging ties out: escalation counts sum to the alert count.

## Data classification, privacy, records

- **Highly Confidential (MNPI / client-confidential).** Portfolio holdings and proposed
  trades can be material non-public information; minimize to what evidences an alert.
- Retain each run's alerts + citations + `config_version` per records policy; log the read,
  the queue emission, and any external-delivery approval.
- Never exfiltrate holdings or trade intentions; route alerts only to approved compliance
  queues.

## Reproducibility

`run_id` binds the pack to the exact inputs, positions `as_of`, and **rule config version**;
re-running with the same inputs and config reproduces the alerts, severities, and
fingerprints. Freshness, precision/recall, threshold behavior, deduplication, and escalation
latency are the primary validation targets for this archetype.
