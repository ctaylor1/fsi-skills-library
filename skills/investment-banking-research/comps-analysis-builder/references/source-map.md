# Source Map — comps-analysis-builder

## Source hierarchy (highest first)

| Rank | Source (MCP integration) | Used for | Access |
| ---- | ------------------------ | -------- | ------ |
| 1 | **Filings / document intelligence** | Reported operating metrics (revenue, EBITDA, EBIT, EPS), share counts, debt/cash from the latest 10-K/10-Q/8-K; page/field citations | Read-only |
| 2 | **Market / financial data** | Share prices (with price date), diluted shares, consensus/forward (FY1) estimates | Read-only |
| 3 | **Research corpus** | Broker/consensus estimates, peer-universe candidates, prior comps sets | Read-only |
| 4 | **CRM** | Deal/coverage context, recorded reviews and approvals | Read-only |
| 5 | **Data room** (deal-specific) | Non-public target figures when the user is wall-crossed and permissioned | Read-only, permission-gated |
| 6 | Approved **peer-selection criteria** + **multiple bands / config** (versioned) | Peer inclusion, outlier bands, freshness threshold | Read-only |

Filings win on conflict for reported fundamentals; market data is the authority on price and
share count; the versioned selection criteria are the authority on which companies are peers.
This skill reads only — it never writes back an analysis, decision, or delivery.

## Citation format

`{system}:{ref}@{date/version}` — e.g. `filings:AAAA-10Q@2026-06-30`,
`marketdata:AAAA@2026-07-15`, `crm:review=PR-88@2026-07-16`, `config:comps@2026.07`.
Every EV bridge and every company multiples row carries a citation; every implied-value row
cites the summary-statistic basis it was derived from. A figure with no citable source is a
missing-metric open item, never an assumed value.

## Freshness / effective dates

- Each company carries a `price_date`. Market data older than `max_price_age_days` (default 5)
  relative to `as_of_date` is marked **stale**: it is still shown and cited, but excluded from
  the summary statistics and raised as a refresh open item.
- Reported fundamentals should be the latest available period; LTM figures must be on a
  consistent period basis across the set.
- `peer_selection_criteria`, the multiple `bands`, and the package template are **versioned
  contracts**; the versions are recorded on the manifest (`config_version`, `template_version`)
  for reproducibility and review.

## Least-privilege operations (deployment)

- `filings.get(ticker, form)` / `docintel.cite(doc_id, field)` → fundamentals + citations — read-only.
- `marketdata.quote(ticker, as_of)` → price, price_date, diluted shares — read-only, bounded.
- `estimates.get(ticker, period)` → forward (FY1) metrics — read-only.
- `crm.read(analysis_id)` → coverage context, recorded reviews/approvals — read-only.
- `config.get('comps-selection'|'comps-bands', version)` — read-only.
No mutation from this skill. The assembled analysis is a **draft**; any delivery or
system-of-record change is a separate, human-approved step via the approval broker. Non-public
figures from the data room are used only when the requesting user is wall-crossed and
permissioned (information-barrier control).
