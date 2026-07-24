# Source Map — bank-product-feature-comparator

## Source hierarchy (highest first)

| Rank | Source (MCP integration) | Used for | Access |
| ---- | ------------------------ | -------- | ------ |
| 1 | **Controlled content library / product catalog** (versioned, owner + effective/expiry per record) | Approved product records: eligibility, fees, features, disclosures, effective dates | Read-only |
| 2 | **Approved-disclosure retrieval** | Filed/approved disclosure documents (Truth in Savings, fee schedules) and their effective dates | Read-only |
| 3 | **Entity resolution** | Resolve a product name/alias to its canonical `product_id` and current version | Read-only |
| 4 | **Data governance — freshness/effective-date service** | Confirm each record is current (effective, not expired, not superseded) as of `as_of` | Read-only |

The **product catalog is the position of record**. A marketing page, a screenshot, a prior
comparison, a colleague's note, or a customer's recollection is **not** an approved source
and must never be substituted for a catalog record. If the catalog and a disclosure conflict,
cite both and fail closed — do not silently reconcile.

## What this skill must NOT source

- Customer profile / needs / risk-tolerance data — this skill does not assess needs or
  suitability, so it does not read or act on that data (see `references/controls.md`).
- Any product not returned as **approved** by the catalog.

## Citation format

`{system}:{ref}#{family}.{attribute}@{effective_date}` — e.g.
`content-lib:product/PROD-CHK-PREMIER;v2#fees.monthly_maintenance@2026-02-01`. Every
comparison cell and every disclosure carries its own citation; the `citation_index` binds
each cited value to the product version and effective date.

## Freshness / effective dates (versioned contract)

- Each product record is a **versioned contract**: `version`, `effective_date`, optional
  `expiry_date`, optional `superseded_by`. The pack records `approved_catalog_version` so a
  comparison is reproducible.
- A record is **usable** only if `approval_status == approved` AND `effective_date <= as_of`
  AND (`expiry_date` absent or `>= as_of`) AND no `superseded_by`. Otherwise the comparison
  **fails closed** — see `references/domain-rules.md`.

## Durable identifiers

- `request_id` is the durable job ID that binds the comparison to the exact requested
  products, `as_of`, and catalog version. Re-running with the same inputs reproduces the
  pack. Downstream handoffs (see `references/handoffs.md`) reference this `request_id`.

## Least-privilege operations (deployment)

- `catalog.get_product(product_id, as_of)` → the current approved record + status + dates.
- `catalog.list_approved(family, as_of)` → approved `product_id`s the banker may compare.
- `disclosure.get(disclosure_id)` → approved disclosure + effective date.
- `entity.resolve_product(name|alias)` → canonical `product_id` + version.

All read-only, deterministic, durable `request_id`, below the fixed timeout. This skill opens
no network connections in this repository; bundled `scripts/` run over de-identified fixtures
under `evals/files/`.
