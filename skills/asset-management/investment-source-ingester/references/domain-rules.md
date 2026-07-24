# Domain Rules — investment-source-ingester

Deterministic rules for classifying entitlement, rejecting non-permitted content, timestamping,
deduplicating, and indexing research sources. Entitlement is a **declared, versioned contract**
(owned by the market-data / research-governance team), never inferred by this skill.

## Entitlement classification (fail closed)

For each source, `scripts/calculate_or_transform.py` reads the declared `entitlement` block and
applies these rules **in order**. Any gap routes the source to the rejected queue — it is never
ingested and permission is never guessed:

| Order | Condition | Outcome |
| ----- | --------- | ------- |
| 1 | `class` absent or blank | **reject** `no_entitlement_declared` |
| 2 | `class == restricted` | **reject** `restricted_content` (never ingest) |
| 3 | `class` not in {`public`,`licensed`,`internal`} | **reject** `unknown_entitlement_class` |
| 4 | `class` ∈ {`licensed`,`internal`} and `grant_ref` blank | **reject** `missing_grant_ref` |
| 5 | `expires` present and `expires < as_of` | **reject** `expired_entitlement` |
| — | otherwise | **accept** with `entitlement_status = permitted` |

`public` still requires an explicit `class: public` declaration; the skill does not assign
`public` from doc_type or origin. Every rejected record keeps its `source_ref`, `doc_type`, and
`reject_reason` in the queue so a human can obtain a grant or discard it. Rejected content is
non-destructive to the queue and never silently dropped.

## Version / effective-date rules

- Record `catalog_version` (the entitlement catalog) on the output; it makes the run reproducible.
- `expires < as_of` (date compare on the first 10 chars) fails the grant closed.
- `ingested_at = as_of` (deterministic). `published_at` / `effective_date` come from the source.

## Deduplication (never merge identities, never overwrite)

- Dedup key: `content_hash`. Sources with the same hash are the same content.
- Within a hash group, the **canonical** copy is chosen deterministically by
  `(authority_rank(doc_type), timestamp, source_ref)` — the highest-authority, earliest,
  lexicographically-first copy wins (see [source-map.md](source-map.md) for ranks).
- Non-canonical copies get `canonical = false` and `duplicate_of = <canonical source_id>`.
  **Both copies keep their own `source_id`.** The ingester never merges two identities into one
  and never overwrites or deletes a source; it links them.

## Durable case / job IDs

- `job_id = isi-{as_of}-{sha1(job_ref)[:8]}` — one ingestion run; idempotent for a given
  `job_ref` + `as_of`.
- `source_id = src-{sha1(source_ref)[:12]}` — durable per source identity; stable across runs.

## Canonical output schema

`index[]` rows: `source_id, source_ref, issuer, doc_type, title, entitlement_status,
entitlement_class, grant_ref, redistribution, published_at, effective_date, ingested_at,
content_hash, language, canonical, duplicate_of`. Plus `rejected[]`, `counts`, `handoff_hints`,
`summary`, `disclaimer`. Validated by `scripts/validate_output.py`.

## Hard boundaries (fail closed)

- **Never ingest unlicensed or restricted content**, and **never infer permission** — permission
  is only ever read from a declared, in-force `grant_ref`.
- **Never merge identities or overwrite a source**; dedup links, it does not consolidate.
- **Never parse financial content, value a security, assign a rating, or state an investment
  view** — this is an index, not analysis. Route normalization/analysis to the adjacent skills in
  [handoffs.md](handoffs.md).

## Handoff hints (suggestions only)

`handoff_hints` maps a canonical source's `doc_type` to a **candidate** downstream skill (e.g.,
`filing` → `financials-normalizer`). These are suggestions a human routes; the ingester does not
parse the content or execute the handoff.
