# Adjacent-Skill Handoffs — fee-and-charge-reviewer

This skill produces a cited **fee-review pack** (`review_id`) with neutral questions and a
remediation-request draft, then stops. It does not decide a refund, act on a fee, adjudicate a
complaint, or file anything.

## Downstream (route the human/reviewer to)

| Downstream skill | When | Handoff artifact |
| ---------------- | ---- | ---------------- |
| `complaint-resolution-assistant` | The customer is filing a complaint and wants a chronology, applicable standards, and a proposed remediation/response | `review_id` + flagged findings |
| `loan-servicing-exception-resolver` | The flagged charge is a **loan-servicing** exception needing root-cause and a staged correction for authorized approval | `review_id` + the loan-side finding |
| `dispute-operations-assistant` | The charge is a **card** transaction dispute (issuer/acquirer), not a fee-vs-schedule question | posted fee + evidence |
| `chargeback-dispute-packager` | Merchant-side card dispute representment | posted fee + evidence |
| `merchant-fee-optimizer` | The user is a **merchant** analyzing interchange/processor pricing, not a consumer account fee | merchant statement + terms |
| `bank-statement-analyzer` | The user wants general statement/cash-flow analysis, not a fee-vs-schedule comparison | account + period |
| `account-anomaly-screener` | The concern is unusual/unauthorized **activity**, not a disclosed-fee comparison | account + focal activity |

## Upstream (may call this skill)

Service-desk and complaint-intake skills may request a fee review pack. A scheduled monitor is
**not** used here (this skill is interactive, `aws-fsi-scheduled-agent: no`).

## Duplicate-execution prevention

- This skill **compares fees to disclosed terms and drafts questions only**; it must not
  decide a refund, reverse/waive/credit a fee, adjudicate a complaint, or file a dispute —
  those belong to the human reviewer and the downstream skills.
- Downstream skills reuse the `review_id` findings rather than recomputing the fee comparison.
