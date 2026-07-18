# Adjacent-Skill Handoffs — bank-statement-analyzer

This skill produces a cited **statement-analysis pack** (`analysis_id`) — extracted income,
recurring obligations, cash-flow trends, fees, and anomalies — and stops. It does not decide,
determine affordability, forecast forward, or resolve fee disputes.

## Downstream (route the human/reviewer to)

| Downstream skill | When | Handoff artifact |
| ---------------- | ---- | ---------------- |
| `loan-affordability-precheck` | User wants an *indicative* affordability estimate from the extracted income/obligations (still not a decision) | `analysis_id` + income/obligation totals |
| `financial-spreading-assistant` | Figures must be spread into a credit-analysis template / tax-return spread | `analysis_id` + extracted rows |
| `cashflow-forecaster` | User wants a forward-looking base/upside/downside projection | `analysis_id` + historical net cash flow |
| `fee-and-charge-reviewer` | Deep fee categorization, disclosure comparison, or a fee dispute | fee rows + evidence |
| `account-anomaly-screener` | User wants fraud/unusual-activity screening with a review-priority band | account + period |
| `credit-application-packager` / `credit-memo-drafter` | Assemble the extracted spread into a lending package/memo | `analysis_id` + spread |

## Upstream (may call this skill)

`customer-onboarding-document-checker`, relationship-manager and service-desk skills may
request a statement analysis. No scheduled monitor is used here (this skill is interactive,
`aws-fsi-scheduled-agent: no`).

## Duplicate-execution prevention

- This skill **extracts and calculates only**; it must not reach a lending/affordability
  decision, forecast forward, or resolve a fee dispute — those belong to the human and the
  downstream skills above.
- Downstream skills reuse the `analysis_id` figures rather than re-extracting from the
  statement, preserving one authoritative source-linked spread.
