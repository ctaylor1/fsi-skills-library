# Adjacent-Skill Handoffs — suitability-reg-bi-reviewer

This skill produces a cited **Reg BI / suitability evidence pack** (`review_id`) and stops. It
does not adjudicate, approve, clear, close, or file. The best-interest / suitability
determination belongs to a qualified human supervisor / principal.

## Downstream (route the human/reviewer to)

| Downstream skill / human | When | Handoff artifact |
| ------------------------ | ---- | ---------------- |
| **Supervisor / principal (human)** | Make the best-interest / suitability determination and any approval | `review_id` + evidence pack |
| `senior-investor-protection-screener` | Customer is a senior / potentially vulnerable investor (diminished capacity, suspected exploitation) | `review_id` + account |
| `conflicts-of-interest-reviewer` | A conflict needs a deeper standalone inventory / mitigation review | conflicts + `review_id` |
| `retirement-income-scenario-modeler` | The rollover needs retirement-income scenario modeling | account + recommendation |
| `portfolio-proposal-comparator` | The real need is comparing two proposals on cost/allocation | the proposals |
| `investment-policy-statement-builder` | The account needs (or lacks) an IPS the recommendation should align to | account + profile |
| `regulatory-exam-response-packager` | The evidence pack is requested for a regulatory exam | `review_id` + evidence |

## Upstream (may call this skill)

`client-review-preparer`, `portfolio-rebalancing-assistant`, `portfolio-proposal-comparator`,
and `advisor-follow-up-assistant` may generate a recommendation that then needs a Reg BI /
suitability evidence review before it reaches a principal. A scheduled monitor is **not** used
here (this skill is interactive, `aws-fsi-scheduled-agent: no`).

## Duplicate-execution prevention

- This skill evaluates and evidences **obligation checks only**; it must not reach a
  best-interest determination, approve/clear/reject the recommendation, place a trade, close the
  review, or file — those belong to the human supervisor/principal and the downstream skills.
- Downstream skills and the supervisor reuse the `review_id` evidence rather than recomputing the
  obligation checks.
