# Adjacent-Skill Handoffs — investment-source-ingester

This skill produces a **canonical source index** (durable `job_id` + per-source `source_id`) and
a **rejected-record queue**, then stops. It does not parse financial content, reconcile values,
enrich identifiers, diff filings, or form any investment view. Those are separate skills; the
ingester emits durable IDs they consume rather than duplicating their work.

## Downstream (route the human/reviewer to)

| Downstream skill | When | Handoff artifact |
| ---------------- | ---- | ---------------- |
| `financials-normalizer` | An indexed filing/release/presentation carries financial statements or schedules that must be standardized to model-ready data | `source_id` + document |
| `security-master-enricher` | Indexed market-data / instrument records need identifier, issuer, classification, or benchmark enrichment | `source_id` + records |
| `investment-vendor-feed-reconciler` | The task is comparing internal vs vendor prices/attributes, not ingesting new sources | vendor + internal `source_id`s |
| `filing-disclosure-change-detector` | The associate wants changed language / new risks between the current and prior filing (this skill only indexes, it does not diff) | current + prior `source_id` |
| `credit-terms-covenant-extractor` | Covenant / terms extraction from an indexed credit document | `source_id` + document |

Each of these skills is R2 and does **not** make a binding decision; they carry their own hard
boundaries (e.g., `financials-normalizer` maps and ties out but does not decide, and borrower
credit-template spreading is a distinct workflow).

## Upstream (may call this skill)

A research associate's workflow, or a research-desk orchestration, requests an ingestion run and
then routes accepted sources onward. A scheduled monitor is **not** used here — this skill is
interactive (`aws-fsi-scheduled-agent: no`).

## Duplicate-execution prevention

- This skill classifies entitlement, timestamps, dedups, and indexes **only**. It never
  normalizes, reconciles, enriches, diffs, or analyzes — downstream skills reuse its
  `source_id`s instead of re-ingesting.
- `handoff_hints` in the output are **candidate** routes (deterministic doc_type → skill map); a
  human confirms and invokes the downstream skill. The ingester never executes a handoff.
- Restricted / undeclared sources are handed to **no** downstream skill — they sit in the rejected
  queue for a human to obtain a grant or discard.
