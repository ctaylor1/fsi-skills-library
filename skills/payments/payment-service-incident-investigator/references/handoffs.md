# Adjacent-Skill Handoffs — payment-service-incident-investigator

Produces a redacted diagnostic evidence pack (`diagnostic_id`) and stops. It does not change
config, rotate keys, disable rules, or deploy fixes.

## Downstream (route the human/engineer to)
| Downstream skill | When | Handoff artifact |
| ---------------- | ---- | ---------------- |
| `payment-integration-readiness-reviewer` | The findings feed a go-live readiness review | integration id + most-frequent category |
| `payment-fraud-control-evaluator` | Failures trace to fraud-rule behavior | integration id + rule ref |

## Upstream (may call this skill)
Payments implementation and support workflows may request a diagnostic pack. This skill is
interactive (`aws-fsi-scheduled-agent: no`).

## Duplicate-execution prevention
- This skill only **classifies and evidences**; it never remediates — configuration changes
  belong to the human and the change process.
- Downstream reuses the `diagnostic_id` pack rather than re-analyzing.

Phase 1 handoff: retain case/participant/rail/jurisdiction, original source references and unresolved issues using payment-contract.md. Validate the target native input independently; renamed skills are not assumed input-compatible. Local IDs and hashes grant no authority and do not persist or accept a case. Only invoke installed capabilities within the requested scope.

Phase 3 routes uncertain individual money outcomes to `payment-repair-planner` under its native exception/authority gate and recovery regression evidence to `payment-integration-readiness-reviewer`. Retain source hashes and unresolved issues; no blind resend.
