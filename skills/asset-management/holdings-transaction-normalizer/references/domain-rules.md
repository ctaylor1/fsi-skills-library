# Domain Rules — holdings-transaction-normalizer

How multi-source holdings/transaction data becomes a canonical dataset **deterministically**,
with lineage, and without ever merging identities or overwriting sources. The mapping ruleset is
a versioned contract owned by investment-data governance; it is not tuned per record or per run.

## Source hierarchy

- For **canonical shape**, the mapping ruleset for each `(source_system, record_type)` is the
  authority (field maps + code enums). Systems covered: `custodian`, `administrator`, `oms`,
  `accounting`.
- For **canonical content (values)**, no source outranks another *inside this skill*. Each source
  record keeps its own values and lineage; the normalizer never reconciles or picks a winner.
  Value conflicts route out (see `references/handoffs.md`).

## Canonical schema & mapping

- Canonical record = `canonical_id` + `record_type` + `lineage{}` + `canonical{}`.
- Required canonical fields per `record_type` are listed in `references/source-map.md` and
  enforced by both `calculate_or_transform.py` and `validate_output.py`.
- Coded values (`side`, `cash_type`, `order_status`, `txn_type`) are translated **only** via the
  ruleset enums. An unmapped code is a `UNMAPPED_CODE_VALUE` reject — never guessed.

## Version & effective-date rules

- **`ruleset_version` is a versioned contract.** Every run records the version used. A mapping or
  enum change is published as a **new version**; the skill never edits a ruleset in place, so a
  historical run remains reproducible under its own version.
- **`source_as_of`** travels with each record. The canonical view never blends records of
  different `source_as_of`, and never back-dates or forward-dates a value.
- **`as_of`** (bundle level) is the run's effective date and is part of the durable `job_id`.
- A run is reproducible: same `bundle_id` + same `ruleset_version` ⇒ identical canonical pack and
  reject queue (records are sorted deterministically).

## Durable case / job IDs

- **`job_id = htn-{bundle_id}-{as_of}`** — durable identifier for the normalization run; binds
  output to inputs + ruleset version; the unit downstream skills reference.
- **`ingest_batch_id = bundle_id`** — groups records of one extract; large bundles split into
  resumable batches under the same id without duplication.
- **`canonical_id = can-{source_system}-{source_record_id}`** — deterministic per-source surrogate
  key, **1:1** with a single source record. It is not a shared or merged identity.
- **Lineage key `(source_system, source_record_id)`** — unique per bundle; a duplicate is a hard
  input error (ambiguous provenance).

## Hard boundaries (fail closed)

- **Never merge identities / deduplicate.** One canonical record ← one source record, one
  `source_record_id`. Identity resolution → `security-master-enricher`.
- **Never overwrite a source.** Immutable `source_hash` per record proves preservation; the
  canonical view is derived and additive.
- **Never choose a canonical value** across conflicting sources → `investment-vendor-feed-reconciler`.
- **Never reconcile / classify breaks / tie out NAV** → `position-cash-reconciliation-assistant`
  / `nav-preparation-tie-out`.
- **Never silently drop or guess.** Every input row is a canonical record or a reason-coded
  reject; the reconciliation must tie out.

## Reject reason taxonomy

`UNMAPPED_SOURCE_SYSTEM`, `UNMAPPED_RECORD_TYPE`, `UNMAPPED_CODE_VALUE`, `UNPARSEABLE_NUMBER`,
`UNPARSEABLE_DATE`, `MISSING_REQUIRED_FIELD`, `AMBIGUOUS_IDENTITY`. Each is a **routing signal to a
human/next skill**, not a disposition. `AMBIGUOUS_IDENTITY` specifically means the source carried
two differing identifiers for one security; the normalizer refuses to pick and routes to the
security master.
