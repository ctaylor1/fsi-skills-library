# Adjacent-Skill Handoffs — payment-integration-readiness-reviewer

Produces a cited readiness packet (`packet_id`) and stops. It does not approve go-live or clear a
launch.

## Downstream (route the human/reviewer to)
| Downstream skill | When | Handoff artifact |
| ---------------- | ---- | ---------------- |
| `payment-service-incident-investigator` | Error behavior needs diagnosis before readiness sign-off | integration id + failing area |
| `payment-fraud-control-evaluator` | Fraud-rule readiness/impact must be assessed | integration id + rule ref |

## Upstream (may call this skill)
Payments implementation workflows may request a readiness packet ahead of a go-live gate. This
skill is interactive (`aws-fsi-scheduled-agent: no`).

## Duplicate-execution prevention
- This skill only **checks readiness and evidences gaps**; it never approves go-live — that
  belongs to the authorized human and the launch process.
- Downstream reuses the `packet_id` evidence rather than recomputing.

Phase 1 handoff: retain case/participant/rail/jurisdiction, original source references and unresolved issues using payment-contract.md. Validate the target native input independently; renamed skills are not assumed input-compatible. Local IDs and hashes grant no authority and do not persist or accept a case. Only invoke installed capabilities within the requested scope.

Use `payment-service-incident-investigator` for service-level consequences and
`payment-operations-improvement-analyzer` for workload and bounded automation business cases.
