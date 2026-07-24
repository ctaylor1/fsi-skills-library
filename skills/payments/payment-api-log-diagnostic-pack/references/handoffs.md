# Adjacent-Skill Handoffs — payment-api-log-diagnostic-pack

Produces a redacted diagnostic evidence pack (`diagnostic_id`) and stops. It does not change
config, rotate keys, disable rules, or deploy fixes.

## Downstream (route the human/engineer to)
| Downstream skill | When | Handoff artifact |
| ---------------- | ---- | ---------------- |
| `payment-integration-readiness-pack` | The findings feed a go-live readiness review | integration id + suspected cause |
| `payment-fraud-rule-impact-analyzer` | Failures trace to fraud-rule behavior | integration id + rule ref |

## Upstream (may call this skill)
Payments implementation and support workflows may request a diagnostic pack. This skill is
interactive (`aws-fsi-scheduled-agent: no`).

## Duplicate-execution prevention
- This skill only **classifies and evidences**; it never remediates — configuration changes
  belong to the human and the change process.
- Downstream reuses the `diagnostic_id` pack rather than re-analyzing.
