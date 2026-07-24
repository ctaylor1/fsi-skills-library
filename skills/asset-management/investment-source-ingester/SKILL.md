---
name: investment-source-ingester
description: >-
  Collect and index only permitted research sources — regulatory filings, issuer releases,
  presentations, earnings-call transcripts, licensed market data, and internal research — by
  classifying each source's declared entitlement, deduplicating by content, timestamping,
  assigning durable IDs, and emitting a canonical source index plus a rejected-record queue.
  Use when a research associate asks to ingest sources, build a source index for an issuer,
  check what content the firm is entitled to use, or dedupe/timestamp filings and transcripts
  before handing them downstream. HARD BOUNDARY: never ingest unlicensed or restricted content
  and never infer permission — it is read only from a declared, in-force grant; undeclared,
  restricted, unknown-class, or expired sources are rejected, not indexed. Never merge
  identities or overwrite sources. Produces no financial normalization, valuation, rating, or
  investment view; hand off normalized financials to financials-normalizer.
license: MIT
compatibility: Amazon Quick Desktop; requires entitlement-catalog, content-hash/fetch, entity-resolution, and research-index MCP integrations (read-only for classification; the library write is approval-gated).
metadata:
  aws-fsi-category: "Asset Management"
  aws-fsi-skill-type: "Utility skills"
  aws-fsi-risk-tier: "R2"
  aws-fsi-archetype: "Domain workflow"
  aws-fsi-agent-pattern: "Interactive decision-support copilot"
  aws-fsi-delivery-wave: "Wave 5 - 2026 industry expansion"
  aws-fsi-action-mode: "Read-only analysis"
  aws-fsi-scheduled-agent: "no"
  aws-fsi-baseline-status: "new"
  aws-fsi-human-approval: "external-delivery"
  aws-fsi-data-classification: "Highly Confidential (MNPI / client-confidential)"
  aws-fsi-jurisdictions: "US (default); configure additional jurisdiction packs per deployment"
  aws-fsi-owner: "Asset Management investment & product"
  aws-fsi-primary-user: "Research associate"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-07-17"
---

# Investment Source Ingester

## Purpose and outcome
Given a manifest of candidate research sources, classify each source's **declared entitlement**,
reject anything not clearly permitted, deduplicate by content, timestamp, assign durable IDs,
and produce a **canonical source index** plus a **rejected-record queue**. A successful output
is a permission-classified, lineage-tracked, deduplicated source list a research associate can
trust and route downstream — with restricted or unlicensed material demonstrably kept out.

## Use when
- "Ingest these sources / build the source index for ACME this quarter."
- "Dedupe and timestamp these filings, transcripts, and decks."
- "Which of these are we actually entitled to use?"
- A workflow needs a clean, cited, durable-ID source list before normalization or analysis.

## Do not use
- **Normalize financial statements** into model-ready data → `financials-normalizer`.
- **Enrich security-master identifiers / classifications** for market data → `security-master-enricher`.
- **Reconcile internal vs vendor** prices/attributes → `investment-vendor-feed-reconciler`.
- **Diff current vs prior filings** for changed language / new risks → `filing-disclosure-change-detector`.
- **Extract covenant / credit terms** from a document → `credit-terms-covenant-extractor`.
- Any request for a **rating, price target, valuation, or buy/sell view** → out of scope; this
  skill indexes sources, it does not analyze them or advise.

## Adjacent-skill handoffs
See [references/handoffs.md](references/handoffs.md). The skill emits a durable `job_id` and
per-source `source_id`; downstream skills consume those IDs. It must not normalize, reconcile,
enrich, diff, or analyze — and it never executes a handoff (a human routes accepted sources).

## Inputs and prerequisites
- A **source manifest** (JSON): `job_ref`, `as_of` (YYYY-MM-DD), `catalog_version`, and
  `sources[]`, each with `source_ref`, `doc_type`, `content_hash`, a timestamp
  (`published_at` and/or `effective_date`), and a declared `entitlement` block
  (`class`, `grant_ref`, `redistribution`, optional `expires`). Schema:
  [scripts/validate_input.py](scripts/validate_input.py).
- Read access to the versioned **entitlement catalog** and upstream content hashes. No live
  connectors are bundled; scripts run over the documented schema and de-identified fixtures.

## Source hierarchy
See [references/source-map.md](references/source-map.md). Authority rank (filing > release >
presentation > transcript > market_data > internal_research) drives the **dedup tie-break
only** — it is never a permission ranking. Permission comes solely from the declared, in-force
`grant_ref`. Cite every row to `{origin}:{source_ref}@{date}` with a durable `source_id`.

## Workflow
1. **Scope & validate** — confirm `job_ref`, `as_of`, and the manifest; run `validate_input`.
   Warnings flag sources that will be rejected (no grant, restricted, duplicate content).
2. **Classify entitlement (deterministic, fail closed)** — for each source, read the declared
   entitlement and apply the ordered rules in
   [references/domain-rules.md](references/domain-rules.md): reject `restricted`, undeclared,
   unknown-class, grant-less licensed/internal, and expired grants to the queue. Permission is
   never inferred.
3. **Assign IDs & timestamp** — durable `job_id` and per-source `source_id`; `ingested_at` set
   deterministically from `as_of`; record `published_at` / `effective_date`.
4. **Deduplicate (link, never merge)** — group accepted sources by `content_hash`; mark the
   highest-authority copy canonical and link the rest via `duplicate_of`. Both keep their IDs.
5. **Index & hint** — run
   [scripts/calculate_or_transform.py](scripts/calculate_or_transform.py) to emit the canonical
   index, the rejected queue, counts, and **candidate** `handoff_hints` (a human routes).

## Validation loop
Run `validate_input` before and [scripts/validate_output.py](scripts/validate_output.py) after.
The output check confirms: full lineage on every row; every row is `permitted` with a valid
class and (for licensed/internal) a grant; no restricted content in the index; unique
`source_id`s with valid `duplicate_of` links; counts tie out; every rejected record has a known
reason; and no advice or inferred-permission language. Fail closed on any miss.

## Human approval
`external-delivery`: human approval is required before the index is **written to a research
library / system of record** or delivered outside the team. The skill itself proposes the index
read-only; internal analytical use may be reviewer-sampled. It never obtains a grant, changes an
entitlement, or ingests restricted content on its own.

## Failure handling
- **Missing/blank entitlement** → reject `no_entitlement_declared`; never guess permission.
- **Restricted or expired grant** → reject `restricted_content` / `expired_entitlement`; keep in
  the queue for a human to obtain a grant or discard.
- **Missing content_hash / timestamp** → structural error from `validate_input`; stop.
- **Ambiguous source identity** → treat as distinct; never merge two `source_ref`s.
- **Tool timeout / large manifest** → page as resumable stages; return the partial index with a
  clear "incomplete" flag; do not drop sources silently.

## Output contract
1. **Summary** — job, `as_of`, counts (accepted / rejected / duplicates).
2. **Index** — per accepted source: `source_id`, lineage, entitlement class + grant, timestamps,
   `canonical` / `duplicate_of`.
3. **Rejected queue** — per rejected source: `source_ref`, `doc_type`, `reject_reason`.
4. **Handoff hints** — candidate downstream skills by doc_type (suggestions; a human routes).
5. **Machine-readable** — the full index JSON with `job_id` for downstream skills.
6. **Standing disclaimer** — "Source index only; entitlement is classified from explicitly
   declared grants and is never inferred. Restricted or undeclared sources are rejected, not
   ingested. No investment advice, valuation, rating, or trading decision is produced."
See [references/controls.md](references/controls.md).

## Privacy and records
Highly Confidential (MNPI / client-confidential). Store only source **metadata + lineage** in the
index — never copy restricted content into it. Respect `redistribution` (`internal_only` /
`prohibited`). Retain the index + rejected queue + `catalog_version` per records policy; log the
read and any external-delivery / library-write approval. Never exfiltrate sources or MNPI.

## Gotchas
- **Permission is declared, not inferred.** A public-looking filing still needs `class: public`;
  a familiar vendor still needs a `grant_ref`. No declaration → rejected.
- **Dedup links, it never merges.** Two copies of one document keep two `source_id`s; the
  duplicate points at the canonical. Never overwrite or delete a source.
- **Authority rank ≠ permission.** Rank only breaks dedup ties; a high-authority source with no
  grant is still rejected.
- **This is an index, not analysis.** No parsing of financials, no valuation, no rating, no
  investment view — route those to the adjacent skills.
- **Reproducibility depends on `catalog_version` + `as_of`.** Record both; `ingested_at` is
  derived from `as_of`, not wall-clock, so runs are deterministic.
