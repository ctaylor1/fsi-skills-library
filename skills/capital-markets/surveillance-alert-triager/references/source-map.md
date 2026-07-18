# Source Map — surveillance-alert-triager

## Source hierarchy (highest first)

| Rank | Source (MCP integration) | Used for | Access |
| ---- | ------------------------ | -------- | ------ |
| 1 | Surveillance alert queue / **case management** | Alert + case state (system of record), dedup, `case_id` | Read-only |
| 2 | **OMS/EMS** (orders, executions) | Trade-surveillance evidence: orders, cancels, fills, notional | Read-only |
| 3 | **Communications archive** (e-comms) | E-comms surveillance evidence: chat/email/voice-transcript lexicon hits | Read-only |
| 4 | **Market / reference data** | Price/venue context, instrument and issuer resolution, benchmark windows | Read-only |
| 5 | **Account / desk context** | Account and desk risk rating, ownership, watch/restricted-list membership | Read-only |
| 6 | **Restricted-list / watch-list** flags | Proximity flag (forces escalation; do not adjudicate) | Read-only |
| 7 | Approved **suppression rule set** + **priority config** (versioned) | Suppression + scoring | Read-only |

## Citation format

`{system}:{ref}@{date/version}` — e.g. `casemgmt:alert=AL-3001@2026-07-15`,
`oms:order=O10@2026-07-11`, `ecomms:msg=M20@2026-07-09`, `config:surv-suppression@v2026.06`.
Every evidence item in a bundle — and every chronology event — carries its own citation.

## Freshness / effective dates

- Alert/case state must be read fresh (avoid working a stale, already-escalated alert).
- Suppression and priority use **versioned** rule/config; the version is recorded on every
  triage record for reproducibility and review.

## Least-privilege operations (deployment)

- `alerts.read(queue|alert_id)`, `cases.find(entity, scenario, period)` (dedup) — read-only.
- `orders.read(account_id, from, to)`, `ecomms.read(entity_id, from, to)` — read-only, bounded.
- `refdata.resolve(instrument|issuer)`, `account.context(entity_id)` — read-only.
- `flags.read(entity_id)` → restricted-list / watch-list proximity (boolean + source), no
  adjudication.
- `config.get('surv-suppression'|'surv-priority', version)` — read-only.
No mutation from this skill. Escalation writes a case-state transition **only** via the
approval broker, recorded as a proposal for the investigator/approver.
