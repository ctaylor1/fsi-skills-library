# Source Map — aml-alert-triager

## Source hierarchy (highest first)

| Rank | Source (MCP integration) | Used for | Access |
| ---- | ------------------------ | -------- | ------ |
| 1 | Transaction-monitoring / **case management** | Alert + case state (system of record), dedup, `case_id` | Read-only |
| 2 | **KYC / customer risk** | Customer profile, risk rating, ownership | Read-only |
| 3 | **Transactions** | Triggering activity, amounts, counterparties, velocity | Read-only |
| 4 | **Sanctions / adverse-media** flags | Proximity flag (route to specialist; do not adjudicate) | Read-only |
| 5 | **Reference data** | MCC/geo/counterparty resolution | Read-only |
| 6 | Approved **suppression rule set** + **priority config** (versioned) | Suppression + scoring | Read-only |

## Citation format

`{system}:{ref}@{date/version}` — e.g. `casemgmt:alert=AL-5521@2026-07-15`,
`txns:acct=****3300;txnid=T-4471@2026-07-11`, `config:aml-suppression@v2026.06`.

## Freshness / effective dates

- Alert/case state must be read fresh (avoid working a stale, already-escalated alert).
- Suppression and priority use **versioned** rule/config; the version is recorded on every
  triage record for reproducibility and review.

## Least-privilege operations (deployment)

- `alerts.read(queue|alert_id)`, `cases.find(entity, rule, period)` (dedup) — read-only.
- `kyc.summary(customer_id)`, `txns.read(account_id, from, to)` — read-only, bounded.
- `flags.read(entity_id)` → sanctions/adverse-media proximity (boolean + source), no
  adjudication.
- `config.get('aml-suppression'|'aml-priority', version)` — read-only.
No mutation from this skill. Escalation writes a case-state transition **only** via the
approval broker, recorded as a proposal for the investigator/approver.
