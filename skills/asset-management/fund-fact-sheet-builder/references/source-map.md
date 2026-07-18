# Source Map — fund-fact-sheet-builder

## Source hierarchy (highest first)

| Rank | Source (MCP integration) | Used for | Access |
| ---- | ------------------------ | -------- | ------ |
| 1 | **Performance system** (GIPS-aligned) | Standardized net-of-fees returns (cumulative, annualized, calendar-year) vs benchmark — **as-of dated** | Read-only |
| 2 | **PMS / OMS** | Holdings, top positions, allocation, fees/charges (OCF/TER, management fee) | Read-only |
| 3 | **Risk / performance analytics** | Volatility, tracking error, Sharpe, drawdown, SRRI/risk indicator | Read-only |
| 4 | **Market data** | Prices, AUM/NAV, time-sensitive figures — **as-of dated** | Read-only |
| 5 | **Controlled-content / compliance-rules library** | Approved regulatory disclosure text (owners, effective dates, expiry) | Read-only |
| 6 | **Research corpus** | ESG classification, methodology notes (no rating/opinion carried through) | Read-only |
| 7 | **Entity resolution** | Fund / share-class / benchmark identity; consistency across figures | Read-only |
| 8 | **Document intelligence** | Field/page citations for extracted figures | Read-only |
| 9 | Fact-sheet **template** + **required sections/approvals/disclosures** config (versioned) | Structure + control gates | Read-only |

The performance system wins on conflict for returns; PMS/OMS is authoritative for holdings and
fees; risk analytics for risk metrics; market data is authoritative for time-sensitive figures
as of its timestamp; the controlled-content library is the only source of approved disclosure
text. This skill **reads only** — it never writes back a fact sheet, a figure, an approval, or a
delivery.

## Citation format

`{system}:{ref}@{date/version}` — e.g. `perf:ret=DGEFAX;1Y@2026-06-30`,
`pms:ocf=DGEFAX@2026-06-30`, `risk:vol=DGEFAX;3Y@2026-06-30`, `mktdata:nav=DGEFAX@2026-06-30`,
`content:disc=past-performance@v2026.05`, `config:factsheet-template@2026.07`.

Every `included`, `stale`, or `unresolved` figure carries a citation. A figure with **no**
citable source is an `unsupported` open item — never an assumed inclusion. Time-sensitive
figures (prices, NAV, risk indicators) must carry an as-of date so staleness is evaluable.

## Source-to-output reconciliation

Every numeric figure may carry both a rendered `value_numeric` and the raw
`source_value_numeric` from its system of record, plus an optional `reconcile_tolerance`
(default 0.05). The assembler ties them out: within tolerance → `reconciled` and eligible to be
asserted; beyond tolerance → a reconcile break, routed to open items and **never asserted**. The
reconciliation ledger records the tie-out for every numeric figure so the draft's numbers are
independently reviewable against source.

## Freshness / effective dates

- Each figure carries `effective_date` and optional `expires`. A figure past its `expires`
  relative to `as_of_date` is marked `stale`, kept cited, and listed as an open item for
  refresh — never silently dropped or presented as current.
- `required_sections`, `required_approvals`, `required_disclosures`, and the fact-sheet template
  are **versioned contracts**; the versions are recorded on the manifest (`config_version`,
  `template_version`) for reproducibility and review.

## Least-privilege operations (deployment)

- `perf.read(fund_id, share_class, period, as_of)` → standardized returns — read-only, bounded.
- `pms.read(fund_id, as_of)` → holdings, fees — read-only, bounded.
- `risk.read(fund_id, metric, as_of)` → risk metrics — read-only.
- `mktdata.read(fund_id|ticker, as_of)` → NAV/price/AUM with timestamp — read-only.
- `content.get(disclosure_id, version)` → approved disclosure text — read-only.
- `entity.resolve(fund|share_class|benchmark)` → identity consistency — read-only.
- `docintel.cite(doc_id, field)` → field/page citations — read-only.
- `config.get('factsheet-template'|'required-approvals'|'required-disclosures', version)` — read-only.

No mutation from this skill. The assembled fact sheet is a **draft**; any external distribution
or system-of-record change is a separate, human-approved step via the approval broker.
