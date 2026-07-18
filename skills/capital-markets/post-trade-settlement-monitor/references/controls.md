# Controls — post-trade-settlement-monitor

- **Risk tier:** R2 — analytical. **Action mode:** Scheduled read-only; alert only.
- **Scheduled agent:** `read-only-monitoring` — one of the approved read-only monitors. It
  runs on a schedule (e.g., intraday cadence + pre-cutoff sweeps), reads sources, thresholds,
  deduplicates, stamps freshness, and **queues** alerts for humans. It never acts.
- **Human approval:** `external-delivery` — required before any alert leaves the internal
  settlement-ops queue (e.g., emailing a counterparty, client, or custodian). Internal
  queueing for the ops reviewer is the default and needs no approval.

## Scheduled read-only, alert-only posture (fail closed)

A scheduled monitor may **enrich, threshold, deduplicate, and queue** — it may **never act,
decide, or close**. Specifically prohibited:

- No **settlement action**: match, affirm, cancel, amend, split, partial, settle, or release
  an instruction or payment.
- No **buy-in / sell-out** initiation, execution, or CSDR penalty dispute submission.
- No **case/alert closure or suppression** outside the deterministic deduplication logic
  (dedup marks a repeat as `duplicate`; it does not close the underlying exception).
- No **counterparty / custodian / client contact** or instruction.
- No **write to any book of record** (OMS, clearing, GL, regulatory report).
- No **binding decision** on whether a fail is at-fault, reportable, or penalty-liable — that
  is a human/authorized-system determination.
- No **threshold tuning to a desk or counterparty**; use only the versioned config.

The monitor **fails closed**: on missing/stale/conflicting data it surfaces the gap and
flags the item rather than guessing or suppressing.

## Required output screens (`scripts/validate_output.py`)

- **Escalation packaging:** every queued item has a severity in {Info, Warning, High,
  Critical} and a non-empty `suggested_route`; every alert has ≥1 cited evidence row.
- **Threshold behavior:** each item's severity equals the deterministic max over its alert
  types' fixed severities (see `domain-rules.md`).
- **Deduplication:** no two active (`new`) alerts share a `dedup_key`; any alert whose key is
  in `deduped_against` is marked `duplicate`, not re-raised.
- **Freshness handling:** a `freshness` block with `as_of` + `max_source_staleness_minutes`;
  items flagged `stale` exactly match `freshness.stale_instruction_ids`.
- **No autonomous action:** `actions_taken` is present and **empty**; no action/decision
  language in the narrative, notes, or alert reasons (regex screen: "initiated a buy-in",
  "cancelled the instruction", "settled the fail", "closed the exception", etc.).
- Standing disclaimer present: "Monitoring alerts only; no settlement action has been taken.
  A human must review, decide, and act."

## Data classification, privacy, records

- **Highly Confidential (customer NPI/PII).** Mask account numbers to last 4; minimize data
  in each alert to what evidences the exception.
- Retain the run + citations + `config_version` per records policy; log the read and any
  external-delivery approval. Never exfiltrate book or counterparty data.

## Reproducibility

`run_id` binds the queue to the exact snapshot, `as_of`, and **config version**; re-running
the same snapshot with the same config reproduces the alerts, severities, and dedup states.
