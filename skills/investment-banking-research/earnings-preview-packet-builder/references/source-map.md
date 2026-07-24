# Source Map - earnings-preview-packet-builder

Every date, figure, KPI, controversy, sensitivity, and debate point in the packet must trace
to an approved source. The skill never originates a number and never states a house view; it
compiles and cites already-sourced facts and third-party-attributed opinions.

## Source hierarchy (highest first)

| Rank | Source (MCP integration) | Used for | Access |
| ---- | ------------------------ | -------- | ------ |
| 1 | **Controlled template library** (versioned) | Approved preview template, required sections, disclaimer set | Read-only |
| 2 | **Issuer filings** (10-K/10-Q/8-K, IR calendar) | Prior guidance (as issued), historical KPIs, disclosed sensitivities, event dates | Read-only |
| 3 | **Earnings-call transcripts** | Guidance language, prior management commentary | Read-only |
| 4 | **Consensus / estimates data** (contributor-aggregated) | Consensus revenue/EPS/segment metrics (third-party, attributed) | Read-only |
| 5 | **Market / financial data** | Trading context, comparable-period figures | Read-only |
| 6 | **Research corpus / news** (approved) | Attributed debate points and known controversies | Read-only |
| 7 | **CRM / coverage context** | Coverage relationship, prior meeting objectives | Read-only |

Consensus is a **third-party aggregate**, cited to its provider; it is never presented as the
skill's estimate. Company guidance is reproduced **as issued**, cited to the filing/transcript.

## Citation format

`{system}:{ref}@{date/version}` - e.g. `consensus:eps@2026-07-18`,
`filing:8-K-guidance-FY26Q2@2026-05-01`, `filing:10-Q-history@2026-05-05`,
`transcript:FY26Q1-call@2026-05-01`, `template:EPP-STD@v2026.05`. Every item records at
least one source; every data point records a `source_ref` and an `attribution`.

## Freshness / effective dates

- The **template** is a versioned contract; `template_id@version` is recorded on the packet
  and the cover/disclaimer items. A superseded template version fails closed.
- Consensus, guidance, KPI, and news figures each carry an as-of date. Consensus is pulled
  fresh before the packet is finalized (estimates drift into the print); a stale pull is
  flagged, not silently carried.
- A figure whose source cannot be confirmed is marked `needs-source` - never back-filled.
- Guidance is quoted **as originally issued** with its issue date; superseded guidance is
  labeled as such, not overwritten.

## Least-privilege operations (deployment)

- `templates.get(template_id, version)`, `templates.list_required_sections(...)` - read-only.
- `filings.read(issuer, form, period)`, `transcripts.read(issuer, event)` - read-only.
- `consensus.read(issuer, metric, as_of)`, `marketdata.read(...)` - read-only, bounded.
- `news.read(issuer, topic)`, `crm.read(coverage_id)` - read-only.
- **No publish / send / distribute / file operation is bound to this skill.** Distribution is
  a human action recorded outside this skill after the required approvals.
