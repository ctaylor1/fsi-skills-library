# Source Map — security-alert-triage-assistant

## Source hierarchy (highest first)

| Rank | Source (MCP integration) | Used for | Access |
| ---- | ------------------------ | -------- | ------ |
| 1 | **SIEM / SOAR** | Alert + case state (system of record), signal ids, correlation, durable `case_id` | Read-only |
| 2 | **CMDB / asset inventory** | Asset resolution, criticality, ownership, internet-facing exposure | Read-only |
| 3 | **IAM / identity** | Identity resolution, privilege level, entitlements | Read-only |
| 4 | **Threat intelligence** | Indicator reputation, severity, known-malicious / active-compromise flags | Read-only |
| 5 | **Vulnerability & cloud posture** | Known-exploited-vulnerability (KEV) nexus, exposure, misconfiguration | Read-only |
| 6 | **Incident & BCP systems** | Existing incidents, business-continuity context for routing | Read-only |
| 7 | Approved **suppression rule set** + **priority config** + **output template** (versioned) | Suppression, scoring, template fidelity | Read-only |

Threat-intel disposition, incident declaration, vulnerability prioritization, cloud-posture
confirmation, and identity/access review are **specialist / IR domains** (see
[handoffs.md](handoffs.md)); this skill consumes their read-only signals as enrichment and
routes for confirmation rather than concluding.

## Citation format

`{system}:{ref}@{date/version}` — e.g. `siem:alert=SA-3001@2026-07-16`,
`cmdb:asset=AST-WEB-11@2026-07-16`, `iam:identity=svc-****-adm@2026-07-16`,
`ti:signature=SIG-C2-BEACON@2026-07-16`, `posture:asset=AST-WEB-11@2026-07-16`,
`config:sec-suppression@sec-triage-2026.07`. Every enriched signal carries at least one
citation; an uncited "present" evidence section is downgraded to an unsupported claim by
[../scripts/validate_output.py](../scripts/validate_output.py).

## Freshness / effective dates

- Alert/case state and threat intelligence must be read **fresh** — a stale IOC reputation or
  an already-escalated alert invalidates the package.
- Asset/identity context is read from CMDB/IAM as-of the triage time; the `as_of` date is
  recorded on every citation.
- The suppression rule set, priority config, and output template are **versioned contracts**;
  their versions are recorded on every package for reproducibility and review.

## Least-privilege operations (deployment)

- `siem.alerts.read(queue|alert_id)`, `siem.cases.find(asset, signature, window)` (correlation) — read-only.
- `cmdb.asset(asset_id)` → criticality, exposure, ownership (read-only).
- `iam.identity(identity_ref)` → privilege, entitlements (read-only).
- `ti.lookup(indicator|signature)` → reputation/severity flags (read-only; no disposition).
- `posture.read(asset_id)` → KEV nexus, exposure (read-only).
- `config.get('sec-suppression'|'sec-priority'|'sec-triage-template', version)` — read-only.

No mutation from this skill. Assembling the package writes **nothing** to a system of record;
the package is a draft proposal for the human analyst, recorded via the approval broker. No
SIEM/SOAR/ticket write, no containment action, no notification is performed here.
