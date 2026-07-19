# Adjacent-Skill Handoffs — portfolio-proposal-comparator

This skill produces a cited, even-handed **proposal comparison pack** (`comparison_id`) and stops. It
does not select, recommend, determine suitability, rebalance, trade, or file — those belong to the
licensed human and the downstream skills.

## Downstream (route the human/reviewer to)

| Downstream skill | When | Handoff artifact |
| ---------------- | ---- | ---------------- |
| `suitability-reg-bi-reviewer` | The advisor has chosen a direction and needs the suitability / Reg BI evidence documented (that skill does not approve the recommendation either) | `comparison_id` + evidence |
| `portfolio-rebalancing-assistant` | A target has been chosen and a drift analysis + proposed trade list is needed | chosen proposal + holdings |
| `investment-policy-statement-builder` | The objectives/constraints/benchmarks the proposals are measured against need to be established or refreshed | client objectives |
| `financial-goal-progress-analyzer` | The question is really goal funding, not proposal comparison | goals + assumptions |
| `retirement-income-scenario-modeler` | The question is retirement-income paths across proposals | proposals + income assumptions |
| `senior-investor-protection-screener` | Exploitation, diminished-capacity, or unusual-disbursement signals appear in the request | client + concern |

## Upstream (may call this skill)

`client-review-preparer` may embed a comparison in a client-review brief; `advisor-follow-up-assistant`
may reference the `comparison_id` in approved meeting notes or follow-ups. A scheduled monitor is **not**
used here (this skill is interactive, `aws-fsi-scheduled-agent: no`).

## Duplicate-execution prevention

- This skill computes and evidences **differences and flags only**; it must not reach a selection,
  suitability determination, trade, or filing — those belong to the human reviewer and the downstream
  skills.
- Downstream skills reuse the `comparison_id` evidence rather than recomputing the comparison.
