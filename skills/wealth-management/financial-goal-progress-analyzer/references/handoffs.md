# Adjacent-Skill Handoffs — financial-goal-progress-analyzer

This skill produces a cited **goal-progress analysis** (`analysis_id`) and stops. It does not
recommend, model decumulation scenarios, stage trades, or assemble the client deck.

## Downstream (route the human/advisor to)

| Downstream skill | When | Handoff artifact |
| ---------------- | ---- | ---------------- |
| `suitability-reg-bi-reviewer` | A recommendation is being considered and needs a Reg BI / suitability evidence review (it does not approve the recommendation) | `analysis_id` + goals + evidence |
| `retirement-income-scenario-modeler` | The client needs decumulation / sequence-risk / withdrawal-strategy modeling with ranges | `analysis_id` + retirement goal inputs |
| `portfolio-rebalancing-assistant` | Drift analysis and a proposed (approval-gated) trade list are needed | dedicated accounts + restrictions |
| `portfolio-proposal-comparator` | Two or more portfolio proposals must be compared | proposals + objectives |
| `client-review-preparer` | The progress read feeds a client-review brief/deck/agenda | `analysis_id` + goals + status bands |
| `advisor-follow-up-assistant` | Meeting notes, action items, and client communications need drafting for advisor approval | `analysis_id` + agreed actions |
| `senior-investor-protection-screener` | Exploitation, diminished-capacity, or unusual-disbursement concerns appear | client context + observed concern |

## Upstream (may call this skill)

`client-review-preparer` may request a progress analysis to embed in a review; an advisor may
invoke it directly. A scheduled monitor is **not** used here (this skill is interactive,
`aws-fsi-scheduled-agent: no`).

## Duplicate-execution prevention

- This skill computes and evidences **goal progress and illustrative levers only**; it must not
  recommend, determine suitability, model scenarios, stage trades, or assemble deliverables —
  those belong to the licensed human and the downstream skills.
- Downstream skills reuse the `analysis_id` evidence rather than recomputing goal progress.
