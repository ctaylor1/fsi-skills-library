# Changelog — investment-source-ingester

## [0.1.0] — 2026-07-20
Initial authoring in the FSI Skills Library (baseline status: `new`; 2026 industry-expansion
cohort, Wave 5). Asset Management / Utility skill; R2, read-only analysis.

- **Scope:** ingest only permitted research sources — filings, releases, presentations,
  transcripts, market data, internal research — by classifying declared entitlement,
  deduplicating by content, timestamping, assigning durable IDs, and indexing. Emits a
  canonical source index + a rejected-record queue.
- **Entitlement (deterministic, fail closed):** permission is read only from a declared,
  in-force `grant_ref`; restricted, undeclared, unknown-class, grant-less licensed/internal,
  and expired sources are rejected to the queue, never ingested. Permission is never inferred.
- **Dedup (link, never merge):** duplicates by `content_hash` are linked via `duplicate_of` to
  the highest-authority canonical copy; each source keeps its own durable `source_id`. Sources
  are never merged, overwritten, or deleted.
- **Controls:** R2; hard boundary against ingesting unlicensed/restricted content, inferring
  permission, merging identities, and producing any financial normalization, valuation, rating,
  or investment view; `external-delivery` approval before any library write.
- **Scripts:** `validate_input` (manifest schema + evaluability warnings), the ingest engine
  (`calculate_or_transform`), and `validate_output` (lineage, entitlement boundary, identity /
  dedup integrity, count tie-outs, rejected-record handling, advice + inferred-permission
  screens, disclaimer). Each carries a `--selftest` over a bundled fixture.
- **Evaluations:** trigger/routing, golden mixed-manifest task, duplicate-not-merged edge,
  deterministic script checks, a fail-closed safety fixture (non-compliant index) + an
  injection scenario, and external-delivery authorization.
- **Handoffs:** downstream to `financials-normalizer`, `security-master-enricher`,
  `investment-vendor-feed-reconciler`, `filing-disclosure-change-detector`, and
  `credit-terms-covenant-extractor`.

### Pending before release
- Domain SME (research governance / market-data licensing) + control-owner blind review.
- Confirm the versioned entitlement-catalog source, its owner, and the redistribution taxonomy.
- Wire read-only MCP integrations (entitlement catalog, content hashing, entity resolution,
  research index) at deployment; the library write stays approval-gated.
