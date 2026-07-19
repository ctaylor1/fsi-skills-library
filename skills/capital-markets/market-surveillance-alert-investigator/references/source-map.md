# Source Map — market-surveillance-alert-investigator

## Source hierarchy (highest first)

| Rank | Source (MCP integration) | Used for | Access |
| ---- | ------------------------ | -------- | ------ |
| 1 | **Surveillance case platform** (case management) | Alert + case state (system of record), escalation provenance, dedup, durable `case_id` | Read-only |
| 2 | **OMS / EMS** (order & execution) | Orders (new/amend/cancel/fill), trades, timestamps, sides, quantities, prices | Read-only |
| 3 | **Market / reference data** | BBO, last, venue volume, benchmark/close windows, instrument reference | Read-only |
| 4 | **Electronic communications archive** | Chat/email/voice-transcript excerpts, flagged terms, channel, timestamps | Read-only |
| 5 | **Account / customer context** | Party ↔ account/desk resolution, role, beneficial ownership | Read-only |
| 6 | **Prior cases / register** | Open & historical cases for the party/instrument (dedup, pattern history) | Read-only |
| 7 | **Surveillance rule + threshold config** (versioned) | Indicator definitions, thresholds, evidence-strength bands | Read-only |

The surveillance case platform is the **system of record** for case state. Order/trade facts
come from OMS/EMS; market context from market data; communications from the comms archive.
Cite **every** evidence item. Thresholds and the strength-band mapping are **versioned
contracts** (see [domain-rules.md](domain-rules.md)).

## Citation format

`{system}:{ref}` — e.g. `casemgmt:surv-case=AL-1001`, `oms:order=O-100-3`,
`trades:trade=T-100-1`, `comms:msg=M-200-1`, `mktdata:XNAS@2026-07-15T15:59:00`.
The config version is recorded on the run so a disposition recommendation is reproducible.

## Freshness / effective dates

- Case/alert state must be read **fresh** — never work a case already closed or re-assigned.
- Escalation provenance (`triage_case_id`, `escalated_by`) is required; investigation
  **consumes an escalation**, it does not re-triage or originate alerts.
- Orders/trades/messages must fall inside the case period; out-of-period events are flagged
  (chronology check) rather than silently merged.
- Thresholds/bands use a **versioned** config; the version is recorded on every bundle.

## Least-privilege operations (deployment)

- `cases.read(case_id)`, `cases.find(party, alert_type, period)` (dedup) — read-only.
- `oms.orders(party_id, instrument, from, to)`, `oms.trades(...)` — read-only, bounded.
- `mktdata.window(symbol, from, to)` — read-only.
- `comms.read(party_id, from, to)` → excerpts + flagged terms, read-only.
- `accounts.resolve(party_id)` — read-only entity resolution.
- `config.get('mktsurv-thresholds', version)` — read-only.

No mutation from this skill. Any case-state transition (escalate, link, or a supervisor's
closure/determination/filing) is a **proposal** carried out **only** through the approval
broker by an authorized human — never by this skill.
