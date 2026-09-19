# Adjacent-Skill Handoffs — account-anomaly-screener

This skill produces a cited **anomaly evidence pack** (`screening_id`) and stops. It does
not investigate to disposition, file, or act.

## Downstream (route the human/reviewer to)

| Downstream skill | When | Handoff artifact |
| ---------------- | ---- | ---------------- |
| `payment-fraud-and-scam-investigator` | Payment-fraud alert needing device/identity/beneficiary network investigation | `screening_id` + focal txns |
| `suspicious-activity-report-drafter` | The reviewer decides a SAR may be warranted (draft-only, human-filed) | `screening_id` + evidence |
| `merchant-chargeback-response-packager` | Merchant-side card dispute | focal txn + evidence |
| `issuer-payment-dispute-reviewer` | Issuer-side consumer-error review; merchant/acquirer representment uses merchant-chargeback-response-packager | focal txn + evidence |
| `bank-statement-analyzer` | The user actually wants cash-flow/statement analysis, not anomaly review | account + period |

## Upstream (may call this skill)

`omnichannel-case-orchestrator` and service-desk skills may request a screening pack; a
scheduled monitor is **not** used here (this skill is interactive, `aws-fsi-scheduled-agent: no`).

## Duplicate-execution prevention

- This skill computes and evidences **signals only**; it must not reach a disposition,
  contact the customer, or take/recommend an account action — those belong to the human
  reviewer and the downstream skills.
- Downstream skills reuse the `screening_id` evidence rather than recomputing signals.
