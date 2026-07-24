# Source Map - investment-vendor-feed-reconciler

## Source hierarchy (for lineage and routing only - NOT for choosing a value)

| Rank | Source (MCP integration) | Used for | Access |
| ---- | ------------------------ | -------- | ------ |
| 1 | **Internal book-of-record** (IBOR / accounting book / security master) | The internal side of every field-level comparison | Read-only |
| 2 | **Vendor market-data feed** (the single vendor under evaluation this run) | The vendor side of every field-level comparison | Read-only |
| 3 | Reconciliation **config** (versioned) | Tolerances, materiality, staleness threshold, per-domain routing | Read-only |
| 4 | Firm **reference-data / pricing hierarchy** policy (versioned) | Documents which source *would* be preferred, and who owns each domain's exceptions | Read-only |
| 5 | Prior-run **reconciliation** (durable `reconciliation_id`) | Carry-forward of open discrepancies | Read-only |

The internal book and the vendor feed are **two independent observations of the same field**;
neither is subordinate to the other for the purpose of this reconciliation. A break is a
disagreement between them. **The ranking above is used only to label lineage and to route an
exception to its owner - it does NOT authorize this skill to select, prefer, or write a
"canonical" value.** Choosing the canonical value is out of scope (see `references/controls.md`).
Run one vendor feed per job; compare additional vendors as separate pairwise runs.

## Input schema (validated by `scripts/validate_input.py`)

Top level: `entity`, `as_of` (YYYY-MM-DD cutoff), `config_version`, `internal_source`,
`vendor_source`, `currency`, `internal_observations[]`, `vendor_observations[]`, `config{}`.

Each observation (`internal_observations[]` / `vendor_observations[]`):
`instrument_id`, `domain` (`price` | `rating` | `index_constituent` | `corporate_action` |
`instrument_attribute`), `field`, `value` (number or string), `as_of` (per-source observation
time), `source_ref`, `currency` (optional), `data_type` (optional: `numeric` | `categorical`).

A **cell** is one `(instrument_id, domain, field)` triple. Each side must carry **at most one**
observation per cell; a repeated cell on one side fails closed (ambiguous pairing).

`config`: `numeric_tolerance_abs`, `numeric_tolerance_pct`, `materiality_pct`, `materiality_abs`,
`staleness_max_age_days`.

## Citation format

`{side}:{source_ref}@{as_of}` - e.g. `internal:ibor;px;INST-A;20260630@2026-06-30T16:00:00Z`
and `vendor:vendorA;eod;INST-A;20260630@2026-06-30T16:00:00Z`. Every break carries lineage
citations to the internal and/or vendor rows it was derived from, each with its **as-of time**.

## Freshness / effective dates

- `config` (tolerances, materiality, staleness, routing) is a **versioned contract**; the output
  records `config_version` so a reconciliation is reproducible.
- `as_of` (job) fixes the cutoff. Each observation's own `as_of` is preserved and surfaced on
  every break; a source older than `staleness_max_age_days` raises a `stale_as_of` break even
  when the values agree.
- Corporate-action fields carry event-effective dates (ex/record/pay); these are compared as
  values, never interpreted or applied here (route to the corporate-action owner).
- `input_fingerprint` (a SHA-256 content hash of the normalized inputs + config) makes the
  `reconciliation_id` a pure function of the inputs - re-running the same inputs is idempotent.

## Least-privilege operations (deployment)

- `ibor.read(entity, as_of, domains)` -> bounded, paged internal observations.
- `vendorfeed.read(vendor_source, as_of, domains)` -> bounded, paged vendor observations.
- `config.get('ivfr', version)` -> tolerances, materiality, staleness, routing map.
- `recon.get(reconciliation_id)` -> prior-run open discrepancies for carry-forward.

All read-only, deterministic, durable `reconciliation_id`, below the fixed timeout; page long
universes as resumable stages. **No write, override, or record-repair operation is bound to this
skill** - discrepancies are surfaced and routed, never resolved here.
