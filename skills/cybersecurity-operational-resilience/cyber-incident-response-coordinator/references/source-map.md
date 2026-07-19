# Source Map — cyber-incident-response-coordinator

## Source hierarchy (highest first)

| Rank | Source (MCP integration) | Used for | Access |
| ---- | ------------------------ | -------- | ------ |
| 1 | **Incident / case management** system (position of record for the incident) | Incident ID, declared status, roles, chronology, decision log | Read-only |
| 2 | **SIEM / SOAR** | Detections, correlation cases, containment actions, timestamps | Read-only |
| 3 | **IAM / identity** | Account/session state, revocations, privileged-access changes | Read-only |
| 4 | **Vulnerability & cloud posture** | Exploited weakness, misconfiguration, exposure evidence | Read-only |
| 5 | **CMDB / service catalog** | Asset criticality, service dependencies, impact tolerances | Read-only |
| 6 | **Threat intelligence** | Actor/TTP context, IOCs (context only, never attribution as fact) | Read-only |
| 7 | **BCP / operational-resilience** register | Critical services, impact tolerances, recovery objectives | Read-only |
| 8 | IR-coordination **config** (versioned) | Mandatory roles, severity mapping, breach-scale threshold | Read-only |

Never substitute a verbal status update for the recorded artifact. If the incident record and
a system log (SIEM/IAM/CMDB) conflict, cite both and flag the discrepancy for the incident
commander — do not silently reconcile.

## Citation format

`{system}:{ref}@{timestamp}` — e.g. `siem:case=IR-8842;alert=A-1@2026-07-17T08:15:00`. Every
chronology entry, evidence item, and decision cites its source system and reference so the
coordination record is reproducible and defensible.

## Freshness / effective dates

- Severity mapping, mandatory roles, and the breach-scale threshold are a **versioned config
  contract**; the pack records `config_version` so a coordination snapshot is reproducible.
- `as_of` stamps the snapshot; overdue tasks and time-in-phase are computed against it.
- Threat-intel attribution is context only and time-decays — never record it as established fact.

## Least-privilege operations (deployment)

- `incident.read(incident_id)` → declared status, roles, chronology, decisions, tasks.
- `siem.case(id)` / `soar.ticket(id)` → detections and response actions with timestamps.
- `iam.state(identity)` → account/session/entitlement state (no credential material).
- `cmdb.service(id)` → dependency graph, criticality, impact tolerance.
- `resilience.register()` → critical services, impact tolerances, recovery objectives.
- `config.get('ir-coord', version)` → mandatory roles + severity mapping + thresholds.

All read-only, deterministic, durable `coordination_id`, below the fixed timeout; page long
chronologies as resumable stages. The skill **stages nothing for execution** and holds no
write, containment, revocation, or filing entitlement.
