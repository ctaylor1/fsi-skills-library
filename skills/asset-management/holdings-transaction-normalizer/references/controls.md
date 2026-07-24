# Controls — holdings-transaction-normalizer

- **Risk tier:** R2 — analytical / utility. **Action mode:** Read-only analysis.
- **Human approval:** `external-delivery` — required before the canonical pack is delivered
  downstream or loaded into any system of record. The skill never writes a system of record.

## Prohibited (fail closed)

- **No identity merge / dedup.** Each canonical record derives from exactly one source record
  and carries exactly one `source_record_id`. Two records that look like the "same" holding stay
  two canonical records. Merging, deduplicating, or minting a shared/master identity is
  prohibited → route to `security-master-enricher`.
- **No source overwrite / mutation.** Sources are read-only; every record keeps an immutable
  `source_hash`. The canonical view is derived and additive, never a rewrite of the input.
- **No value selection across conflicting sources.** The normalizer does not choose which price,
  rating, attribute, or corporate-action term is correct → `investment-vendor-feed-reconciler`.
- **No reconciliation / matching / break classification** → `position-cash-reconciliation-assistant`
  / `nav-preparation-tie-out`.
- **No silent drops or guesses.** Every input row is either a canonical record or a reject with a
  reason code; the reconciliation count must tie out.
- **No investment advice, valuation, or trade recommendation.**

## Required output screens (`scripts/validate_output.py`)

- Reconciliation ties out: `input == canonical + rejected`, and each count equals the actual
  list length.
- Every canonical record: complete lineage envelope; unique `canonical_id`; a **scalar**
  `source_record_id` (a list / merge separator / `merged_from` fails closed); required canonical
  fields for its `record_type`; no source-mutation flag.
- Every rejected record: `reason_code`, `reason`, `source_record_id`, `source_hash`.
- Free-text screen: no merge/overwrite/value-selection/advice assertions (regex over
  narrative/notes only, so negated boundary language in the disclaimer/reject reasons is not
  mis-flagged).
- Standing disclaimer present.

## Reject reason taxonomy (deterministic)

`UNMAPPED_SOURCE_SYSTEM`, `UNMAPPED_RECORD_TYPE`, `UNMAPPED_CODE_VALUE`, `UNPARSEABLE_NUMBER`,
`UNPARSEABLE_DATE`, `MISSING_REQUIRED_FIELD`, `AMBIGUOUS_IDENTITY`. Each names the human/next-skill
owner; none is a disposition.

## Data classification, privacy, records

- **Highly Confidential (MNPI / client-confidential).** Minimize carried fields to the approved
  canonical schema; do not copy unrelated identifiers or free-text notes.
- Retain the canonical pack, reject queue, and `ruleset_version` per records policy; log the read
  and any external-delivery approval.

## Reproducibility

`job_id` + `ruleset_version` bind the output to the exact inputs and mapping contract; re-running
the same bundle with the same ruleset reproduces the canonical pack and reject queue byte-for-byte
(records are sorted deterministically).
