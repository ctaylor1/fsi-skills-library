# Source Map — holdings-transaction-normalizer

## Source systems (all read-only)

| Rank for *shape* | Source (MCP integration) | Record types | Access |
| ---------------- | ------------------------ | ------------ | ------ |
| ruleset-defined | **Custodian** feed | position, cash | Read-only |
| ruleset-defined | **Fund administrator** feed | position, cash, transaction | Read-only |
| ruleset-defined | **OMS/EMS** | order | Read-only |
| ruleset-defined | **Accounting / GL** | transaction, cash | Read-only |
| authority for mapping | **Controlled mapping ruleset** (versioned) | field maps + code enums | Read-only |

**No source outranks another for content.** This skill normalizes *shape and codes*; it does not
decide which source's *value* is correct when they differ. Each source record keeps its own
values and its own lineage. Selecting a canonical value is `investment-vendor-feed-reconciler`;
reconciling records is `position-cash-reconciliation-assistant` / `nav-preparation-tie-out`;
resolving identities is `security-master-enricher`.

## Canonical schema (approved shape)

Every canonical record: `canonical_id`, `record_type`, `lineage{...}`, `canonical{...}`.

| record_type | Required canonical fields | Optional |
| ----------- | ------------------------- | -------- |
| `position` | account_id, security_id, quantity, currency | cost_basis, market_value |
| `cash` | account_id, currency, amount | cash_type |
| `order` | account_id, order_ref, side, security_id, quantity, currency | order_status |
| `transaction` | account_id, txn_ref, txn_type, amount, currency, trade_date | security_id, quantity, settle_date |

`security_id` is carried **as provided by the source** — it is not resolved, enriched, or
cross-walked here.

## Lineage envelope (on every canonical and rejected record)

`source_system`, `source_record_id`, `source_as_of`, `ingest_batch_id`, `ruleset_version`, and
an immutable `source_hash` (sha256 of the source record). The `source_hash` is the proof that
the source was preserved, not overwritten.

## Citation / identifier format

- **Lineage key:** `(source_system, source_record_id)` — unique per bundle; a duplicate is a
  hard input error (ambiguous provenance).
- **Canonical id:** `can-{source_system}-{source_record_id}` — deterministic, **1:1** with a
  single source record. It is a per-source surrogate key, never a merged/shared identity.
- **Job id:** `htn-{bundle_id}-{as_of}` — durable; binds the output to the exact inputs +
  ruleset version so a run is reproducible.

## Freshness / effective dates

- `source_as_of` travels with each record; the canonical view never blends records of different
  `source_as_of` into one.
- `ruleset_version` is a **versioned contract**; the output records the version used. A mapping
  change is a new version, not an in-place edit.

## Least-privilege operations (deployment)

- `custodian.read(...)`, `administrator.read(...)`, `oms.read(...)`, `accounting.read(...)` →
  bounded, paged extracts; read-only.
- `ruleset.get('canonical-mapping', version)` → field maps + enums.
All read-only, deterministic, durable `job_id`, below the fixed timeout; page large bundles as
resumable batches keyed by `bundle_id`. No write, no network retry, no identity/value resolution.
