# Source Map — insurance-regulatory-filing-packager

## Source hierarchy (highest first)
| Rank | Source (MCP integration) | Used for | Access |
| ---- | ------------------------ | -------- | ------ |
| 1 | Filing-management (SERFF/equivalent) record (system of record) | Filing header, components, submission status | Read-only |
| 2 | Actuarial **exhibit** data | Indicated rate change, supporting exhibits | Read-only |
| 3 | Approved **filing-checklist config** (versioned) | Required components/exhibits, notice rule | Read-only |
| 4 | Reference data | State/line normalization | Read-only |

Never let a component flag override the filing-management record; if they conflict, cite both
and escalate.

## Citation format
`{system}:{ref}@{ts/version}` — e.g. `filing:filing=RATE-2231;component=actuarial_memo@2026-07-18`,
`checklist:rate@v2026.05`. Every gap cites its evidence line and the checklist rule/version.

## Freshness / effective dates
- Checklist config is a **versioned contract**; the output records the version used.
- Effective-date/notice lead is computed from the filing `as_of` to `effective_date`.

## Least-privilege operations (deployment)
- `filing.read(filing_id)` → header + components — read-only, bounded.
- `actuarial.read_exhibits(filing_id)` → indicated change + exhibits — read-only.
- `config.get('filing_checklist', type, version)` → required items/notice rule — read-only.
Durable `packet_id`; below the fixed timeout; no mutation.
