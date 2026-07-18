# Adjacent-Skill Handoffs — collections-treatment-planner

This skill produces a cited **treatment-plan recommendation pack** (`plan_id`) and stops. It
does not adjudicate, offer, set up, execute, file, or close anything — those are the
specialist's decisions and, where a system change is needed, a separate approval-gated skill.

## Downstream (route the human/specialist to)

| Downstream skill | When | Handoff artifact |
| ---------------- | ---- | ---------------- |
| `vulnerable-customer-support-assistant` | Enhanced-care case: vulnerability indicators need specialist accommodation and referral | `plan_id` + vulnerability context |
| `loan-affordability-precheck` | Sizing a payment arrangement needs indicative affordability with assumptions/stress cases | disclosed income/expenses |
| `bank-statement-analyzer` | Affordability/cash-flow must be substantiated from statements | account + period |
| `cashflow-forecaster` | A forward view of the customer's ability to pay is needed | transaction history + assumptions |
| `loan-servicing-exception-resolver` | An **approved** treatment (e.g., due-date change, re-age, forbearance) must be staged and executed under authorization (R4) | approved treatment + `plan_id` |
| `complaint-resolution-assistant` | The customer disputes the delinquency as an error or raises a complaint | complaint context |

## Upstream (may call this skill)

Servicing and casework skills may request a treatment plan for a delinquent account. No
collections-specific triage skill exists in the catalog, so upstream routing is otherwise a
human/operations hand-in; this skill is interactive (`aws-fsi-scheduled-agent: no`).

## Non-catalog / human handoffs (prose — do not invent a skill)

- **Attorney-represented / litigation / bankruptcy / SCRA (servicemember)** cases → route to
  the appropriate licensed specialist or legal/compliance team; this skill only flags the
  suppression and stops.
- **Non-profit credit-counseling referral** → an external agency, not a skill; the plan may
  recommend offering the referral for the specialist to make.
- **Credit-bureau dispute / correction** → the authorized bureau-reporting team.

## Duplicate-execution prevention

- This skill computes **eligibility and recommendations only**; it must not adjudicate, offer,
  set up, execute, file, report, or close — those belong to the human specialist and to the
  approval-gated `loan-servicing-exception-resolver`.
- Downstream skills reuse the `plan_id` recommendation rather than recomputing eligibility.
