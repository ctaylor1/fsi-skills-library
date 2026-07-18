# Source Map — market-landscape-researcher

## Source hierarchy (highest first)

| Rank / tier | Source (MCP integration) | Used for | Access |
| ----------- | ------------------------ | -------- | ------ |
| 1 | **Regulatory filings & official statistics** (SEC/EDGAR, exchange filings, government/central-bank statistics) via approved-source retrieval | Reported financials, market-share anchors, macro/IT-spend series, regulatory text | Read-only |
| 2 | **Licensed research & market data** (industry trackers, analyst research, deal databases) via approved-source retrieval | Market sizing, share estimates, technology and transaction trends | Read-only |
| 3 | **Reputable business press & trade media** | Directional/qualitative context, recent events, consolidation narrative | Read-only |
| 4 | **Company marketing / unverified web** | Leads and color only — **never** the sole support for a load-bearing figure | Read-only |

Additional read-only inputs at deployment: **document intelligence** (filing/deck citation),
**entity resolution** (company/security/vendor de-duplication), **CRM / data room** (deal
context and permissioned documents), and **controlled content library** (versioned
disclaimer + jurisdiction language).

Prefer the highest-tier source that supports a claim. Where sources disagree (e.g., two share
estimates), cite both, state the range, and do not silently pick one.

## Citation format

`{publisher}:{source_id}@{date}` — e.g. `IDC:S2@2026-05-15`. Every finding in every one of the
eight dimensions carries a citation resolving to a row in `sources[]`. Competitor shares carry
the `source_id` they were reconciled from. The config version and `as_of` bind the brief to a
point in time so it is reproducible.

## Freshness / effective dates

- `staleness_days` (default 365) flags sources older than that window relative to `as_of`;
  stale sources are listed in `evidence_coverage.stale_sources` and must be refreshed before
  external delivery.
- Market shares, sizing, and technology/transaction items move quickly — record `as_of` and
  the source date on every load-bearing figure and re-verify near delivery.
- Thresholds (HHI bands, staleness window) are a **versioned config contract**, not a per-deal
  judgment; the brief records `config_version`.

## Least-privilege operations (deployment)

- `filings.get(entity, form, period)` → bounded filing sections + citations.
- `research.query(theme, geography, as_of)` → licensed tracker/analyst rows (paged).
- `entity.resolve(name|ticker|vendor)` → normalized identifiers (avoid double-counting).
- `deals.query(sector, window)` → M&A / capital-markets activity rows.
- `content.get('landscape-disclaimer', version)` → approved disclaimer + jurisdiction text.

All read-only, deterministic, bounded payloads, below the fixed timeout; page long corpora as
resumable stages and carry the durable `landscape_id`.
