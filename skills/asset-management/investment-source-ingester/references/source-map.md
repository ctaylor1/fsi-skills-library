# Source Map — investment-source-ingester

## Source hierarchy (authority, highest first)

The rank is the source-of-record authority used for **dedup tie-break** (when two accepted
copies share a content hash, the highest-authority copy is marked canonical). It is **not** a
permission ranking — permission always comes from the declared entitlement, never from rank.

| Rank | doc_type | Typical origin | Notes |
| ---- | -------- | -------------- | ----- |
| 1 | `filing` | Regulatory filing (e.g., SEC EDGAR) | Position of record for financial statements |
| 2 | `press_release` | Issuer press release / results release | Issuer-published |
| 3 | `presentation` | Issuer investor deck / supplement | Issuer-published |
| 4 | `transcript` | Earnings-call / event transcript | Usually vendor-licensed |
| 5 | `market_data` | Prices, index constituents, reference data | Vendor-licensed; redistribution-limited |
| 6 | `internal_research` | Internal notes / models | Internal entitlement, restricted distribution |

Never substitute a lower-authority copy for a filing of record when both are present; keep
the filing canonical and link the vendor copy as a duplicate (identities are preserved, not
merged).

## Entitlement is declared, never inferred

Every source carries an `entitlement` block: `class` ∈ {`public`, `licensed`, `internal`,
`restricted`}, plus `grant_ref` (the named license/authorization), `redistribution`, and an
optional `expires`. The ingester **reads** this block; it never derives permission from the
doc_type, the issuer, or the fetch location. A source with no declared, in-force grant is
**rejected to the queue**, not ingested. See [domain-rules.md](domain-rules.md).

## Citation / lineage format

`{origin}:{source_ref}@{published_or_effective_date}` — e.g.
`edgar:edgar/ACME/10-Q/2026-05-08@2026-05-08`. Every index row carries a durable `source_id`,
its `source_ref`, `content_hash`, timestamps, and the `grant_ref` under which it was ingested.

## Freshness / effective dates

- The **entitlement catalog** (`catalog_version`) is a versioned contract; the output records
  the version so an ingestion run is reproducible. A grant with `expires < as_of` is rejected
  (`expired_entitlement`).
- Each source records `published_at` and/or `effective_date`; `ingested_at` is set
  deterministically from `as_of` (not wall-clock) so re-running a job reproduces the index.
- `job_id = isi-{as_of}-{sha1(job_ref)[:8]}` and `source_id = src-{sha1(source_ref)[:12]}`
  are durable; re-running the same job over the same sources yields the same IDs (idempotent).

## Least-privilege operations (deployment)

- `entitlement.catalog(version)` → the declared grants/redistribution terms for candidate sources.
- `content.hash(source_ref)` → the content hash used for dedup (computed upstream at fetch).
- `research.index.write(job_id, rows)` → append-only write of accepted rows (system-of-record
  write; `external-delivery` approval; the skill itself only proposes the index).
All read-only for classification; deterministic; durable `job_id`/`source_id`; below the fixed
timeout; page large manifests as resumable stages. No live connectors are bundled in this repo
— `scripts/` operate over the documented JSON schema and de-identified fixtures.
