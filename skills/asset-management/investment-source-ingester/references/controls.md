# Controls — investment-source-ingester

- **Risk tier:** R2 — analytical / utility. **Action mode:** Read-only analysis (proposes an
  index; the library write is a separate, approved system-of-record step).
- **Human approval:** `external-delivery` — required before the index is written to a research
  library / system of record or delivered outside the team. Reviewer sampling for internal use.

## Prohibited (fail closed)

- **No ingestion of unlicensed or restricted content.** A `restricted` class, an undeclared or
  unknown class, a licensed/internal source without a `grant_ref`, or an expired grant is
  **rejected**, never indexed.
- **No inferred permission.** Permission is only read from a declared, in-force `grant_ref`; the
  skill never derives it from doc_type, issuer, or origin.
- **No identity merge or overwrite.** Dedup links duplicates via `duplicate_of`; each source keeps
  its own `source_id`. Sources are never consolidated, overwritten, or deleted.
- **No investment view.** No rating, price target, valuation, buy/sell/hold view, or trade idea —
  this skill indexes sources; it does not analyze them.
- **No content parsing beyond metadata.** Financial statement extraction/normalization and
  security-master enrichment belong to the adjacent skills in [handoffs.md](handoffs.md).

## Required output screens (`scripts/validate_output.py`)

- Every index row has a durable `source_id`, `source_ref`, `content_hash`, a timestamp
  (`published_at` or `effective_date`), and `ingested_at` (lineage).
- Every index row is `entitlement_status = permitted` with class ∈ {public, licensed, internal};
  a `restricted` (or otherwise non-permitted) row is a hard failure; licensed/internal rows carry
  a `grant_ref`.
- `source_id`s are unique (identities never merged); every `duplicate_of` points at a canonical
  member present in the index and is not self-referential.
- `counts.{accepted,rejected,duplicates}` tie out to the arrays.
- Every rejected record carries a `source_ref` and a known `reject_reason`.
- No investment-advice/decision language and no inferred-permission language in free-text fields.
- The standing disclaimer is present.

## Data classification, privacy, records

- **Highly Confidential (MNPI / client-confidential).** Internal research and any MNPI-bearing
  source is restricted-distribution; respect `redistribution` (`internal_only`/`prohibited`).
- Store only source metadata + lineage in the index; do not copy restricted content into it.
- Retain the index + rejected queue + `catalog_version` per records policy; log the read and any
  external-delivery / library-write approval.

## Reproducibility

`job_id` binds the run to `job_ref` + `as_of`; `source_id` binds each row to its `source_ref`.
Re-running the same manifest under the same `catalog_version` reproduces the index, the dedup
decisions, and the rejected queue exactly.
