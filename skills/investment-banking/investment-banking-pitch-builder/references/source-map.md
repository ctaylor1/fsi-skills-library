# Source Map - investment-banking-pitch-builder

Every figure, chart, and claim in the assembled draft must trace to an approved source. The
skill never originates numbers; it assembles and cites already-approved components.

## Source hierarchy (highest first)

| Rank | Source (MCP integration) | Used for | Access |
| ---- | ------------------------ | -------- | ------ |
| 1 | **Controlled template library** (versioned) | Approved pitch template, required sections, disclaimer set | Read-only |
| 2 | **Approved analysis/model artifacts** (upstream skills) | Comps, DCF, three-statement, merger/LBO, scenarios, profiles, market pages | Read-only |
| 3 | **Filings & market/financial data** | Reported financials, trading data, precedent transactions | Read-only |
| 4 | **Research corpus** | Sector/theme context (approved, non-selective) | Read-only |
| 5 | **CRM / client context** | Relationship history, mandate, audience | Read-only |
| 6 | **Data room** (where engaged) | Diligence-sourced facts (via the diligence pack) | Read-only |

## Citation format

`{system}:{ref}@{date/version}` - e.g. `comps:peer-set@2026-07-15`,
`dcf:base-case@2026-07-14`, `template:IB-PITCH-STD@v2026.05`, `filing:10-K-2025@2026-03-01`.
Every page records at least one source; every claim records a `source_ref`.

## Freshness / effective dates

- The **template** is a versioned contract; the `template_id@version` is recorded on the
  draft and the cover/disclaimer pages. A superseded template version fails closed.
- Market/trading data and comps carry an as-of date; stale inputs are flagged, not silently
  carried. Re-pull from the upstream analysis skill rather than editing figures in place.
- A claim whose source cannot be confirmed is marked `needs-source` - never back-filled.

## Least-privilege operations (deployment)

- `templates.get(template_id, version)`, `templates.list_required_sections(...)` - read-only.
- `artifacts.get(component, ref)` for approved comps/DCF/model/profile/market pages - read-only.
- `marketdata.read(...)`, `filings.read(...)`, `crm.read(engagement_id)` - read-only, bounded.
- `dataroom.read(doc_ref)` via the diligence pack - read-only.
- **No send / deliver / distribute / file operation is bound to this skill.** Delivery is a
  human action recorded outside this skill after the required approvals.
