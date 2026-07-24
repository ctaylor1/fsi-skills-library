---
name: holdings-transaction-normalizer
description: >-
  Normalize positions, cash, orders, and transactions from custodian, fund-administrator, OMS,
  and accounting/GL schemas into the firm's approved canonical schema, attaching per-record
  lineage (source system, source record id, source as-of, ruleset version, immutable source
  hash) and routing anything unmappable to a rejected-record queue with reason codes. Output
  canonical JSON/CSV plus the reject queue and a reconciliation count. Use when an
  investment-data operations analyst needs to standardize multi-source holdings/transaction
  extracts for downstream reconciliation, NAV tie-out, or reporting, or asks to map,
  canonicalize, or normalize custodian/administrator feeds with lineage and a reject queue.
  HARD BOUNDARY: never merge identities, deduplicate, or overwrite source records; never choose
  a canonical value across conflicting sources, resolve a security identity, reconcile to
  custodian, or give investment advice — route those to the adjacent skills and a human.
license: MIT
compatibility: Amazon Quick Desktop; requires read-only custodian, fund-administrator, OMS, and accounting/GL feed integrations plus a controlled, versioned mapping-ruleset service and entity-resolution reference data. Deterministic stdlib-only scripts over documented JSON schemas + de-identified fixtures; no live connectors, network, or retries in this repository.
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
  aws-fsi-primary-user: "Investment-data operations analyst"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-07-17"
---

# Holdings & Transaction Normalizer

## Purpose and outcome
Given a bundle of positions, cash, orders, and transactions exported from **multiple source
schemas** (custodian, fund administrator, OMS, accounting/GL), map each source record **1:1**
into the firm's approved **canonical schema**, attach full **lineage**, and route anything that
cannot be mapped deterministically to a **rejected-record queue** with a reason code. A
successful output is a canonical dataset (JSON/CSV) plus the reject queue plus a reconciliation
count that ties out — ready for a human to review and, once approved, for downstream
reconciliation, NAV tie-out, or reporting to consume. The normalizer standardizes *shape and
codes*; it never adjudicates *truth* (which value, which identity, whether records match).

## Use when
- "Normalize/map/canonicalize these custodian and administrator position files into our
  canonical schema."
- "Convert the OMS order extract and the accounting transaction/cash feed to the canonical
  holdings schema with lineage and a reject queue."
- "Standardize this multi-custodian holdings dump so downstream reconciliation and NAV tie-out
  can consume one shape."
- An analyst needs a reproducible, source-linked canonical dataset with every unmappable row
  accounted for (never silently dropped).

## Do not use
- The user wants to **choose the correct value** when sources disagree (price, rating,
  corporate-action term, attribute) → `investment-vendor-feed-reconciler`. This skill never
  picks a canonical value across conflicting sources.
- The user wants to **merge/resolve identities** or create a master security/account, or two
  records are "the same" under different identifiers → `security-master-enricher` (steward
  approval). **HARD BOUNDARY** — this skill emits both records and flags the conflict; it never
  merges.
- The user wants to **reconcile/match** internal records to custodian/prime-broker/administrator
  and classify breaks → `position-cash-reconciliation-assistant`; or **tie out NAV** across
  books/administrator → `nav-preparation-tie-out`.
- The user wants **data-quality anomaly detection** (stale prices, implausible moves, duplicate
  instruments, broken mappings across feeds) → `investment-data-quality-exception-detector`.
- Any **investment advice**, valuation, or trade recommendation → out of scope for this library.

## Adjacent-skill handoffs
See [references/handoffs.md](references/handoffs.md). This skill emits a canonical pack keyed by
a durable `job_id`, plus a reject queue whose reason codes name the correct downstream owner
(e.g. `AMBIGUOUS_IDENTITY` → `security-master-enricher`). Downstream skills consume the canonical
records and lineage; they do not re-run normalization, and this skill does not perform their
reconciliation, value selection, or identity resolution.

## Inputs and prerequisites
- An **ingest bundle** (`bundle_id`, `as_of`, `ruleset_version`, `records[]`). Each record
  carries `source_system`, `record_type`, `source_record_id`, `source_as_of`, and a raw
  `payload`. Schema and readiness checks: [scripts/validate_input.py](scripts/validate_input.py).
- The **versioned mapping ruleset** for the source systems/record types in the bundle (field
  maps + code enums). Absent an inline ruleset, the documented default
  (`canon-ruleset-2026.07`) is used and its version is recorded. See
  [references/domain-rules.md](references/domain-rules.md).
- Read access to the source feeds; no write access to any system of record is required or used.

## Source hierarchy
See [references/source-map.md](references/source-map.md). For canonical *shape*, the mapping
ruleset is the authority for each `(source_system, record_type)`. For canonical *content*, no
source outranks another inside this skill — the normalizer keeps each source record's own values
and lineage and never reconciles them. Every canonical field is traceable to exactly one source
record via `lineage.source_record_id` and an immutable `source_hash`.

## Workflow
1. **Validate the bundle** — run `validate_input`. Fail closed on missing envelope fields,
   non-object payloads, bad dates, or a duplicate `(source_system, source_record_id)` lineage
   key. Warnings flag rows that will land in the reject queue.
2. **Normalize (deterministic)** — run
   [scripts/calculate_or_transform.py](scripts/calculate_or_transform.py). For each record:
   look up the field map for its `(source_system, record_type)`; translate coded values via the
   ruleset enums; coerce numbers/dates; check required canonical fields. Attach lineage +
   `source_hash`. Assign a deterministic per-source `canonical_id` (1:1 — **not** a merge).
3. **Route rejects** — any record that cannot be mapped (unknown system/type, unmapped code,
   unparseable number/date, missing required field, or an **ambiguous identity**) goes to the
   reject queue with a reason code and its source snapshot. Nothing is guessed, merged, or
   dropped.
4. **Reconcile counts** — assert `input == canonical + rejected`; surface the tie-out.
5. **Validate the output** — run [scripts/validate_output.py](scripts/validate_output.py) and
   fail closed on any miss (see below). Present the canonical pack + reject queue + disclaimer.

## Validation loop
Run `validate_input` before and `validate_output` after. The output gate confirms: reconciliation
ties out (no silent drops); every canonical record has a complete lineage envelope, a unique
`canonical_id`, a **single** `source_record_id` (no identity merge), and required fields for its
type; sources are preserved (immutable `source_hash`, no overwrite flag); every reject carries a
reason code and source hash; no prohibited merge/overwrite/value-selection/advice language is
present; and the standing disclaimer is present. Correct and re-run until clean, or fail closed.

## Human approval
`external-delivery`: human review and approval are required before the canonical pack is
**delivered downstream or loaded into any system of record**. Producing and reviewing the pack
is read-only analysis and needs no approval. The skill never writes a system of record itself.

## Failure handling
- **Unmappable record** → route to the reject queue with the specific reason code; never guess
  a mapping or coerce silently.
- **Conflicting identifiers within a record** → `AMBIGUOUS_IDENTITY` reject; route to
  `security-master-enricher`. Do **not** pick or merge.
- **Sources disagree on a value** (two custodian vs administrator positions) → keep **both**
  canonical records with their own lineage; do not reconcile — that is
  `position-cash-reconciliation-assistant` / `nav-preparation-tie-out`.
- **Duplicate lineage key** in the bundle → input validation error (ambiguous provenance); stop
  and have the source re-exported.
- **Missing ruleset** → use the documented default and record its version; if a source
  system/record type is genuinely unknown, reject those rows rather than inventing a map.
- **Tool timeout / large bundle** → split the bundle into resumable batches keyed by
  `bundle_id`; the transform is deterministic so partial batches recombine without duplication.

## Output contract
1. **Canonical pack** — `job_id`, `bundle_id`, `as_of`, `ruleset_version`, `input_record_count`,
   `canonical_records[]` (each with `canonical_id`, `record_type`, `lineage{...}`, `canonical{...}`),
   `rejected_records[]` (each with `reason_code`, `reason`, `source_record_id`, `source_hash`),
   and `reconciliation{input, canonical, rejected}`.
2. **Canonical/CSV export** — the same canonical records flattened per `record_type` for tools
   that prefer CSV; lineage columns travel with every row.
3. **Standing disclaimer** — "Derived canonical view with lineage; no source record was merged
   or overwritten and no reference-data conflict, identity, or reconciliation was resolved. Not
   an investment recommendation."
See [references/controls.md](references/controls.md).

## Privacy and records
MNPI / client-confidential. Minimize payload fields carried into canonical output to those the
approved schema defines; do not copy free-text notes or unrelated identifiers. Retain the
canonical pack, reject queue, and `ruleset_version` per records policy so a run is reproducible;
log the read and any external-delivery approval. Never exfiltrate holdings data or move it to an
unapproved destination.

## Gotchas
- **Two records for the "same" holding are not a bug.** A custodian and an administrator
  position for the same account/security are **two** canonical records by design — merging them
  is the security master's/reconciliation's job, not the normalizer's.
- **Normalizing shape is not resolving truth.** Mapping `B`→`buy` is in scope; deciding which of
  two disagreeing prices is right is not.
- **Reason codes are routing.** `AMBIGUOUS_IDENTITY`, `UNMAPPED_CODE_VALUE`, and
  `MISSING_REQUIRED_FIELD` each point a human at the right next step; keep them specific.
- **The ruleset is a versioned contract.** Record `ruleset_version` on every run; a mapping
  change is a new version, never an in-place edit that silently reshapes history.
- **Never overwrite the source.** The `source_hash` proves the input was preserved; the canonical
  view is derived, additive, and reversible to its source.
