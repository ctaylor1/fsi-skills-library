# Controls — counterparty-exposure-monitor

- **Risk tier:** R2 — analytical. **Archetype:** Monitor & alert.
- **Action mode:** `Scheduled read-only; alert only` (`aws-fsi-scheduled-agent: read-only-monitoring`).
- **Human approval:** `external-delivery` — required before an alert pack is delivered
  outside the review queue or written to a system of record.

## Scheduled read-only, alert-only posture (fail closed)

This skill runs on a schedule against read-only sources. It may **aggregate, threshold,
tag freshness, deduplicate, and enqueue** alerts for a human queue. It may **never**:

- **act** — post/recall collateral, call margin, reduce/raise a limit, terminate/novate a
  trade, unwind/hedge exposure, block or suspend a counterparty, or settle/cancel a trade;
- **decide** — make or communicate a binding counterparty, credit, or trading decision;
- **close or suppress** — close, resolve, or suppress an alert outside the deterministic
  dedup logic; a stale feed never causes an exposure to be dropped;
- **write a system of record** — positions, limits, collateral, ratings, or the risk book.

The only write it performs at deployment is appending an alert to the **human review
queue** (`queue.enqueue`). Every disposition beyond that is a human action.

## Required output screens (`scripts/validate_output.py`)

- Every alert has a `fingerprint`, a valid `severity` (Warning/Breach/Critical), a
  `freshness` tag (current/stale), a `status` (new/recurring), and ≥1 cited evidence row.
- **Deduplication:** alert fingerprints are unique; the same underlying breach does not
  appear twice. `status` marks whether the fingerprint was already open (`recurring`).
- **Freshness handling:** each feed in `stale_feeds` has a matching `data_freshness` alert;
  no stale input is silently suppressed; a stale-tagged alert cannot claim a current feed.
- **Escalation/queue packaging:** each alert's `queue`, `sla_hours`, and `escalate_to`
  match the deterministic severity mapping (see domain-rules.md).
- **run_severity** equals the max alert severity (deterministic tie-out).
- **No autonomous-action language** anywhere in narrative/notes/reasons (regex screen:
  "posted collateral", "reduced the limit", "terminated the", "auto-resolved", "closed the
  alert", "suspended the counterparty", etc.).
- **Standing disclaimer** present: "Monitoring alert only; no limit, trade, collateral, or
  counterparty action has been taken. Human review is required before any action."

## Escalation latency

Severity drives a queue and an SLA target only; the SLA is a **human** response target, not
an automated action deadline. Critical → urgent queue (1h), Breach → risk queue (4h),
Warning → watch queue (24h). Missing an SLA never triggers an automated action.

## Data classification, privacy, records

- **Highly Confidential (MNPI / client-confidential).** Exposure levels, counterparty
  ratings, and CDS reactions can be market-moving; treat as need-to-know.
- Minimize counterparty data in output to what evidences an alert. Do not restate MNPI
  beyond the alert's evidence rows.
- Retain the alert set + citations + `config_version` per records policy; log the read and
  any `external-delivery` approval.

## Reproducibility

`run_id` binds the alert set to the exact inputs, feed timestamps, and **config version**;
re-running with the same inputs and config reproduces the alerts, severities, fingerprints,
and freshness tags.
