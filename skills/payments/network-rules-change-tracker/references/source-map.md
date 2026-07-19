# Source Map - network-rules-change-tracker

## Source hierarchy (highest first)

| Rank | Source (MCP integration) | Used for | Access |
| ---- | ------------------------ | -------- | ------ |
| 1 | **Card-network / payment-scheme bulletin feed** (Visa, Mastercard, Nacha, RTP, ...) | Obligations, effective dates, version, publisher signature | Read-only |
| 2 | **Rule / change taxonomy** (versioned) | Trusted `networks`, `readiness_bands`, `min_lead_days`, category definitions | Read-only |
| 3 | **Product / process / control / contract / system inventories** | Mapping book of record - resolves each obligation's declared impacts | Read-only |
| 4 | **Owner registry** | Owner traceability (valid accountable owners) | Read-only |
| 5 | **Implementation tracker** | Readiness - status and target date per obligation | Read-only |
| 6 | **Prior open-alert store** | Deduplication of already-open items across runs | Read-only |

The **authoritative bulletin is the definition of record** for every obligation and effective
date. Never infer an obligation, date, or mapping from an unverified bulletin, a reviewer's
assertion, or a prior run. If a bulletin cannot be authenticated (untrusted publisher, unverified
signature, or missing version/source), flag it and mark its derived alerts `unverified_source` -
do not treat it as in force. If the inventories and a bulletin disagree on scope, cite both and
raise the gap; do not resolve it silently.

## Citation format

`{system}:{ref}@{date}` - e.g.
`feed:bulletin=RTP-BUL-2026-033;network=RTP@2026-07-18`,
`bulletin:bulletin=MC-BUL-2026-221;obligation=OBL-1@2026-07-18`,
`inventory:obligation=OBL-1;domains=system@2026-07-18`,
`inventory:obligation=OBL-1;owner=merchant-ops@2026-07-18`,
`tracker:bulletin=NACHA-BUL-2026-007;obligation=OBL-1;status=in_progress@2026-07-18`, and each
alert cites the taxonomy category with its config version,
`taxonomy:category=readiness@network-rules-cfg-2026.07`. Every alert cites the measured evidence
row(s) and the taxonomy (with its `config_version`).

## Freshness / effective dates

- The taxonomy is a **versioned contract** (`config_version`); the pack records the version so a
  run is reproducible and an exception can be tied to the exact bands and trusted-publisher set
  in force.
- Each bulletin carries an `effective_date`; the monitor computes `days_to_effective` against the
  run `as_of` and classifies readiness by the versioned `readiness_bands`.
- The **feed** carries `feed_as_of`; the monitor computes staleness against
  `max_feed_staleness_days`.
- **Stale / unauthenticated inputs are flagged, never suppressed.** A stale feed raises a
  freshness alert and marks every alert `stale_input`; an unauthenticated bulletin raises an
  authenticity alert and marks its derived alerts `unverified_source`. Results are treated as
  low-confidence pending refreshed / verified inputs, not silently dropped.

## Least-privilege operations (deployment)

- `bulletins.list(as_of, since)` -> new/updated bulletins with signature + version metadata.
- `taxonomy.get(config_version)` -> trusted networks, readiness bands, min lead days.
- `inventory.get(category)` -> products / processes / controls / contracts / systems (paged).
- `owners.list()` -> valid accountable owner registry.
- `tracker.status(bulletin_id, obligation_id)` -> implementation status and target date.
- `alerts.open(config_version)` -> previously-open alert fingerprints for deduplication.

All read-only, deterministic, below the fixed timeout, with a durable `run_id`. Page large feeds
and inventories as resumable stages. The monitor writes **nothing** back to any system of record -
it only emits alerts and queue items for human review.
