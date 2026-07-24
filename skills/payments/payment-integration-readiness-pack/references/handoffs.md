# Adjacent-Skill Handoffs — payment-integration-readiness-pack

Produces a cited readiness packet (`packet_id`) and stops. It does not approve go-live or clear a
launch.

## Downstream (route the human/reviewer to)
| Downstream skill | When | Handoff artifact |
| ---------------- | ---- | ---------------- |
| `payment-api-log-diagnostic-pack` | Error behavior needs diagnosis before readiness sign-off | integration id + failing area |
| `payment-fraud-rule-impact-analyzer` | Fraud-rule readiness/impact must be assessed | integration id + rule ref |

## Upstream (may call this skill)
Payments implementation workflows may request a readiness packet ahead of a go-live gate. This
skill is interactive (`aws-fsi-scheduled-agent: no`).

## Duplicate-execution prevention
- This skill only **checks readiness and evidences gaps**; it never approves go-live — that
  belongs to the authorized human and the launch process.
- Downstream reuses the `packet_id` evidence rather than recomputing.
