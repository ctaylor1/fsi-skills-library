# Source Map — operational-resilience-scenario-tester

## Source hierarchy (highest first)

| Rank | Source (MCP integration) | Used for | Access |
| ---- | ------------------------ | -------- | ------ |
| 1 | **Important-business-service register + impact-tolerance standard** (position of record) | Service scope, impact tolerances (max downtime / data loss), owners | Read-only |
| 2 | **CMDB / service dependency map** | People, process, technology, facilities, third-party, and data dependencies per service | Read-only |
| 3 | **Incident & BCP systems** (exercise records) | Response decisions, timestamps, recovery evidence, lessons | Read-only |
| 4 | **SIEM/SOAR, IAM, vulnerability & cloud-posture, threat intelligence** | Scenario grounding (threat plausibility), observed recovery telemetry | Read-only |
| 5 | Resilience-programme **config** (versioned) | Severity/plausibility rubric, tolerance metrics, coverage dimensions, disposition thresholds | Read-only |

Never substitute an assertion of readiness for the recorded exercise evidence. If the
register, CMDB, and exercise record conflict (e.g., a dependency mapped in CMDB but never
exercised), cite each and flag the gap for the reviewer; do not resolve it silently.

## Citation format

`{system}:{ref}@{date}` — e.g. `bcp:exercise=EX-2026-04;decision=D-1` or
`siem:exercise=EX-2026-04;artifact=failover-log`. Every scenario's decisions and recovery
evidence cite the specific exercise artifact.

## Freshness / effective dates

- The rubric, tolerance metrics, coverage dimensions, and disposition thresholds are a
  **versioned contract** (`config_version`); the pack records the version used so a test is
  reproducible.
- Impact tolerances are effective-dated in the register; use the value in force at `as_of`.
- Exercise evidence must post-date the last material change to the service; stale evidence
  is a coverage gap, not a pass.

## Least-privilege operations (deployment)

- `register.read(service_id, as_of)` -> important business service + effective impact tolerance.
- `cmdb.dependencies(service_id)` -> mapped dependency dimensions.
- `bcp.exercise(exercise_id)` -> decisions, recovery evidence, lessons.
- `telemetry.recovery(service_id, exercise_id)` -> observed downtime / data-loss metrics.
- `config.get('opres', version)` -> rubric + thresholds + coverage dimensions.

All read-only, deterministic, durable `test_id`, below the fixed timeout; page long
programmes into resumable per-service or per-scenario stages. No write, submission, or
regulator-facing operation is bound by this skill.
