# Source Map — phishing-and-bec-investigator

## Source hierarchy (highest first)

| Rank | Source (MCP integration) | Used for | Access |
| ---- | ------------------------ | -------- | ------ |
| 1 | **SIEM / SOAR / case management** | Reported message, incident/case state (system of record), dedup, `case_id` | Read-only |
| 2 | **Email security gateway** | Raw headers, authentication results (SPF/DKIM/DMARC), URLs, attachment metadata | Read-only |
| 3 | **IAM / directory** | Sender/recipient identity resolution, exec/VIP watchlist, recent auth events | Read-only |
| 4 | **Threat intelligence** | Domain/URL/hash reputation, known-bad IOCs, campaign correlation | Read-only |
| 5 | **Vendor / payment reference data** | Approved vendor bank registry (BEC beneficiary verification) | Read-only |
| 6 | **CMDB / cloud posture** | Affected assets, mailbox exposure scope | Read-only |
| 7 | Detection **scoring + watchlist config** (versioned) | Risk scoring, impersonation watchlist, known corporate domains | Read-only |

## Citation format

`{system}:{ref}@{date/version}` — e.g. `soar:incident=PH-3001@2026-07-15`,
`gw:msgid=<bec-3001@mail>;headers.authentication-results@2026-07-15`,
`ti:domain=0urbank.com@2026-07-15`, `config:phish-scoring@phish-2026.07`. Every indicator,
chronology event, and amount in the evidence bundle carries a citation to its source.

## Freshness / effective dates

- Incident/case state must be read fresh (avoid re-investigating an already-linked or
  already-escalated report).
- Authentication verdicts and IOC reputation are point-in-time; record the observation time.
- Scoring, the impersonation watchlist, and the known-domain / vendor-bank registries are
  **versioned contracts**; the config version is recorded on every investigation.

## Least-privilege operations (deployment)

- `incidents.read(report_id|queue)`, `cases.find(from_addr, subject, period)` (dedup) — read-only.
- `gw.headers(message_id)`, `gw.auth_results(message_id)`, `gw.urls|attachments(message_id)` — read-only.
- `iam.resolve(address)`, `iam.watchlist()` — read-only, bounded.
- `ti.reputation(domain|url|hash)`, `vendors.bank_registry()` — read-only.
- `config.get('phish-scoring'|'known-domains'|'impersonation-watchlist', version)` — read-only.

No mutation from this skill. Containment (block, quarantine, credential reset), payment
recall, and case closure are **proposed** to the approval broker / downstream skills as
recommendations; they are never executed here.
