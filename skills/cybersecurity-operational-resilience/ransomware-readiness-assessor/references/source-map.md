# Source Map — ransomware-readiness-assessor

## Source hierarchy (highest first)

| Rank | Source (MCP integration) | Used for | Access |
| ---- | ------------------------ | -------- | ------ |
| 1 | **CMDB / service registry** (position of record for critical services) | Critical-service inventory, tier, dependency mapping, service-to-asset links | Read-only |
| 2 | **Backup / recovery platform** | Backup existence, immutability/offline-copy state, last restore-test evidence | Read-only |
| 3 | **IAM / PAM** | Privileged-account counts, MFA enforcement, administrative-tiering model | Read-only |
| 4 | **SIEM / SOAR / EDR** | Detection-coverage signals across critical-service assets | Read-only |
| 5 | **Vulnerability & cloud-posture** | Exposure and configuration signals that inform readiness context | Read-only |
| 6 | **Threat intelligence** | Ransomware TTP context orienting which controls matter (informational) | Read-only |
| 7 | **Third-party / vendor-risk register** | Critical-third-party resilience and recovery-commitment evidence | Read-only |
| 8 | **GRC / exercise register** | Ransomware tabletop / IR / backup-restore exercise history | Read-only |
| 9 | **BCP / incident & crisis-comms** | Crisis-communication plan, out-of-band channel, last test | Read-only |
| 10 | **Readiness config** (versioned) | Thresholds and intervals (restore-test, exercise, coverage, MFA ratio) | Read-only |

The **CMDB critical-service record is the position of record** for what is in scope; the
backup/recovery platform is the position of record for backup and restore-test state. When a
service asserts a control (e.g. "backups are immutable") but the backup platform shows
otherwise, that conflict IS the finding — cite both, never resolve it silently or assume one
system is stale.

## Citation format

`rra:{source_ref}[@{date}]` — e.g. `rra:cmdb=svc;id=SVC-PAY@2025-06-01`. Every fired gap cites
the specific service/control rows and, where relevant, the effective date (last restore test,
last exercise, last comms test) behind it. Staged remediation candidates reference the target
and the fired finding that motivates them.

## Freshness / effective dates

- The readiness **config** (intervals, thresholds, relevant exercise types) is a **versioned
  contract**; the output records `config_version` so an assessment is reproducible.
- `last_restore_test`, `last_conducted` (exercise), and `last_tested` (comms) are
  effective-dated; a **missing** date is treated **conservatively as stale/overdue** and
  flagged, never silently ignored.
- Absence of positive control evidence (no `segmented`, no `backup`, no `dependency_map`) is
  treated conservatively as a **gap** ("no evidence of the control"), not as compliant.
- The assessment is a point-in-time snapshot at `as_of`; re-running with the same extract and
  config version reproduces the findings, staged candidates, and priority.

## Least-privilege operations (deployment)

- `cmdb.critical_services(scope)` → services with tier, segmentation, dependency-map flag.
- `backup.state(service_id)` → backup existence, immutability/offline copy, last restore test.
- `iam.privileged_posture(scope)` → privileged counts, MFA coverage, tiering flag.
- `edr.coverage(service_id)` → detection-coverage fraction for the service's assets.
- `trm.critical_vendors(scope)` → critical-third-party resilience/recovery evidence.
- `grc.exercises(scope)` / `bcp.comms(scope)` → exercise and crisis-comms posture.
- `config.get('rw-readiness', version)` → thresholds + intervals + relevant exercise types.

All read-only, deterministic, durable `readiness_id`, below the fixed timeout; page large
scopes as resumable stages. The skill never calls a remediation/change operation — staging a
remediation is producing a **candidate record**, not invoking a write.
