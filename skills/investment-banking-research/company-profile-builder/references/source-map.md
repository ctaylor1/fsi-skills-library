# Source Map — company-profile-builder

## Source hierarchy (highest first)

| Rank | Source (MCP integration) | Used for | Access |
| ---- | ------------------------ | -------- | ------ |
| 1 | **Filings / EDGAR** (10-K/10-Q/8-K, proxy) | Business overview, ownership, management, reported financials, precedent transactions | Read-only |
| 2 | **Market / financial data** | Trading data (price, market cap, EV, multiples, 52-week range) — time-sensitive, **as-of dated** | Read-only |
| 3 | **Research corpus** (approved internal/published) | Operating KPIs, segment metrics, background (no rating/opinion carried through) | Read-only |
| 4 | **Entity resolution** | Company/ticker/subsidiary identity; consistency across facts | Read-only |
| 5 | **Document intelligence** | Field/page citations for extracted facts | Read-only |
| 6 | **CRM** | Relationship/context metadata (never a substitute for a filed source) | Read-only |
| 7 | **Data room** | Deal-confidential facts — **often MNPI**; excluded from external profiles | Read-only |
| 8 | Profile **template** + **required sections/approvals** config (versioned) | Structure + control gates | Read-only |

Filings win on conflict for issuer facts; market data is authoritative for trading data as of
its timestamp. Data-room facts are frequently MNPI and are gated by information-barrier
controls. This skill **reads only** — it never writes back a profile, a decision, or a delivery.

## Citation format

`{system}:{ref}@{date/version}` — e.g. `filings:10-K@2026-03-31`,
`mktdata:px=DMCO@2026-07-16`, `research:note=R-118@2026-06-30`,
`dataroom:doc=DR-22@2026-07-10`, `config:profile-template@2026.07`.

Every `included`, `stale`, or `unresolved` fact carries a citation. A fact with **no** citable
source is an `unsupported` open item — never an assumed inclusion. Trading-data citations must
carry an as-of date so staleness is evaluable.

## Freshness / effective dates

- Each fact carries `effective_date` and optional `expires`. A fact past its `expires`
  relative to `as_of_date` is marked `stale`, kept cited, and listed as an open item for
  refresh — never silently dropped or presented as current.
- `required_sections`, `required_approvals`, and the profile template are **versioned
  contracts**; the versions are recorded on the manifest (`config_version`, `template_version`)
  for reproducibility and review.

## Least-privilege operations (deployment)

- `filings.get(company_id, form, period)` / `docintel.cite(doc_id, field)` → issuer facts +
  citations — read-only.
- `mktdata.read(ticker, as_of)` → trading data with timestamp — read-only, bounded.
- `research.get(note_id)` → approved KPI/background facts (no rating carried) — read-only.
- `entity.resolve(name|ticker)` → identity consistency — read-only.
- `crm.read(company_id)`, `dataroom.get(doc_id)` → context / deal-confidential facts — read-only.
- `config.get('profile-template'|'required-approvals', version)` — read-only.

No mutation from this skill. The assembled profile is a **draft**; any external distribution or
system-of-record change is a separate, human-approved step via the approval broker.
