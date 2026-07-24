# Adjacent-Skill Handoffs — payment-fraud-rule-impact-analyzer

Produces an illustrative sample impact estimate (`analysis_id`) and stops. It does not deploy,
enable, or roll out a rule, and makes no live decision.

## Downstream (route the human/analyst to)
| Downstream skill | When | Handoff artifact |
| ---------------- | ---- | ---------------- |
| `payment-integration-readiness-pack` | The rule change is part of a go-live readiness review | integration id + rule ref |
| `payment-api-log-diagnostic-pack` | Production errors need diagnosis (not a rule estimate) | integration id |

## Upstream (may call this skill)
Fraud-strategy workflows may request an impact estimate before proposing a rule change. This skill
is interactive (`aws-fsi-scheduled-agent: no`).

## Duplicate-execution prevention
- This skill only **estimates on a sample**; it never deploys a rule or decisions a live
  transaction — those belong to the human and the deployment process.
- Downstream reuses the `analysis_id` estimate rather than recomputing.
