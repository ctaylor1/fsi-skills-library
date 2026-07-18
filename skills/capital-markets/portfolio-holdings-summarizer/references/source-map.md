# Source Map — portfolio-holdings-summarizer

All figures in the summary must cite one of the sources below, ranked. See the shared
platform services in [`docs/SHARED-SERVICES.md`](../../../../docs/SHARED-SERVICES.md).

## Source hierarchy (highest first)

| Rank | Source (MCP integration) | Used for | Access |
| ---- | ------------------------ | -------- | ------ |
| 1 | Portfolio-accounting / custody **position of record** | Quantities, market value, cost basis, as-of date | Read-only |
| 2 | Official **brokerage statement** for the period | Reconciling positions, statement page/line citations | Read-only (document-intelligence) |
| 3 | **Reference/market data** | Asset-class/sector classification, prices where the file is silent, FX rates | Read-only |
| 4 | User-provided export/file | Only when 1–3 unavailable; must be labeled as unverified | Read-only |

Never let a user assertion override the position of record. If sources conflict, present
both with citations and stop for human review.

## Citation format

Each position and metric carries a citation of the form
`{system}:{ref}@{as_of}` — e.g. `custody:acct=****1234;lot=CUSIP037833100@2026-06-30` or
`statement:p3,line12@2026-06-30`. The machine-readable output stores the citation per
position; the narrative references them inline where a figure is stated.

## Freshness / effective dates

- Every position must carry an **as-of date**; the summary states a single reporting date.
- Prices older than the configured staleness window (default: > 1 business day for liquid
  instruments) are labeled **stale** and excluded from "priced total" unless the user
  accepts them.
- FX conversion requires a cited rate and as-of; otherwise report per currency.

## Least-privilege operations (deployment)

- `positions.read(account_id, as_of)` → normalized position list (bounded page size).
- `refdata.classify(instrument_id)` → asset class / sector.
- `refdata.price(instrument_id, as_of)` → price + source + timestamp.
All read-only, deterministic schemas, durable `snapshot_id`, below the fixed timeout.
