# Source Map — coverage-meeting-preparer

## Source hierarchy (highest first)

| Rank | Source (MCP integration) | Used for | Access |
| ---- | ------------------------ | -------- | ------ |
| 1 | **CRM** | Relationship history, interactions, mandates, open items (system of record for the relationship) | Read-only |
| 2 | **Filings** | Company facts: results, guidance, capital structure, maturities | Read-only |
| 3 | **Transcript** | Management commentary, strategic-review signals, tone | Read-only |
| 4 | **Market/financial data** | Price/volume moves, trading context | Read-only |
| 5 | **Research corpus** | Internal sector notes, comparables context (cited, not recomputed) | Read-only |
| 6 | **News** | Public developments and corroboration | Read-only |
| 7 | **Data room** | **Private-side / MNPI** deal material (barrier-controlled) | Read-only |
| 8 | **Controlled template & approved-source list** (versioned) | Brief template, section order, approved systems, standing note | Read-only |

CRM is authoritative for the relationship and who the counterparty is; filings/transcripts and
market data are authoritative for company facts; the data room supplies private-side material
that must stay behind the information barrier. The approved brief template and the
approved-source list are **versioned contracts** — record which `config_version`/template and
`as_of_date` every brief was built from. Never state a fact, development, figure, or objective
that a listed, approved source does not support.

## Citation format

`{system}:{ref}@{date}` — e.g. `crm:acct=NWM;interactions@2026-07-15`,
`filings:NWM 10-Q FY26 Q2@2026-07-08`, `transcript:NWM Q2 earnings call@2026-07-09`,
`marketdata:NWM px/vol 1M@2026-07-16`, `research:sector note MAT-2026-14@2026-07-05`,
`dataroom:mgmt refinancing memo@2026-07-12` (private-side / MNPI).

Only systems on the **approved-source list** (`crm`, `filings`, `transcript`, `research`,
`marketdata`, `news`, `dataroom`, `comps` by default) may back a claim. A claim whose citation
resolves to no in-inventory source, or to a system not on the approved list, is
**unsupported** and blocks packaging.

## Freshness / effective dates

- Every source carries a `date`. A source older than `freshness_days` (default 45) relative to
  `as_of_date` is **stale**; if it is cited and not explicitly acknowledged (`stale_ack: true`),
  the meeting is flagged `stale-source` and not packaged.
- Deliberately historical context (e.g., a prior mandate) is acknowledged with `stale_ack: true`
  so it does not block, while still recording its age.
- The brief always records the `as_of_date` it was assembled against.

## MNPI / information-barrier handling

- A source with `classification: "mnpi"`, or a content item flagged `mnpi: true`, is
  **private-side / internal-only**. It may inform internal preparation but must never be placed
  in an externally-shareable field.
- Any MNPI in the record forces `control_room_clearance` to be **recorded as approved** before
  the draft is relied on; absent that, the record is held `barrier-hold`.

## Least-privilege operations (deployment)

- `crm.get_relationship(account_id)` / `crm.list_interactions(account_id)` — read-only.
- `filings.get(ref)` / `transcript.get(ref)` / `marketdata.get(symbol, window)` — read-only,
  bounded.
- `research.get(note_id)` / `news.search(entity, window)` — read-only.
- `dataroom.get(ref)` — read-only, **private-side**; access logged and barrier-controlled.
- `templates.get('coverage-brief', version)` / `config.get('cmp-approved-sources', version)` —
  read-only controlled content.

No mutation from this skill. Sending, distributing, filing, posting to CRM, and any external
delivery are **out of scope** — performed by an authorized human after review and the recorded
approvals.
