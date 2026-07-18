# Adjacent-Skill Handoffs — portfolio-exposure-analyzer

This skill produces a cited **exposure pack** (`exposure_id`) and stops. It does not
adjudicate mandate compliance, model stressed liquidity, or take/recommend any portfolio
action.

## Downstream (route the human/reviewer to)

| Downstream skill | When | Handoff artifact |
| ---------------- | ---- | ---------------- |
| `mandate-compliance-monitor` | The reviewer needs an actual guideline/mandate/regulatory test of exposures or a proposed trade, and exception escalation | `exposure_id` + findings |
| `liquidity-stress-analyzer` | The question shifts to liquidation horizons, market impact, redemption coverage, or stressed liquidity | `exposure_id` + liquidity buckets |
| `counterparty-exposure-monitor` | The question is counterparty/settlement/derivative/collateral exposure and limit monitoring | `exposure_id` + relevant positions |
| `performance-attribution-builder` | The user wants what drove **return** (allocation/selection/factor), not current exposure | portfolio + period |
| `fund-commentary-drafter` | The exposure/positioning read feeds monthly/quarterly commentary | `exposure_id` + positioning summary |
| `fund-fact-sheet-builder` | Exposure breakdowns feed a controlled fact-sheet draft | `exposure_id` + exposure tables |
| `investment-committee-memo-builder` | Exposure evidence feeds an IC memo | `exposure_id` + findings |

## Upstream (may call this skill)

`investment-committee-memo-builder`, `fund-commentary-drafter`, `fund-fact-sheet-builder`,
and `due-diligence-questionnaire-responder` may request an exposure pack as a cited input. A
scheduled monitor is **not** used here (this skill is interactive,
`aws-fsi-scheduled-agent: no`).

## Non-catalog handoffs (human / operations / licensed specialist)

- **Portfolio manager** — owns any decision to change positioning; this skill only informs.
- **Investment guidelines / risk oversight** — owns limit definitions and the versioned
  config; questions about *what the limit should be* go here, not to this skill.
- **Compliance officer** — owns the formal mandate-compliance determination and any
  regulatory filing.

## Duplicate-execution prevention

- This skill computes and evidences **exposures and limit findings only**; it must not reach
  a compliance disposition, model stressed liquidity, or take/recommend a trade — those
  belong to the human, `mandate-compliance-monitor`, and `liquidity-stress-analyzer`.
- Downstream skills reuse the `exposure_id` evidence rather than recomputing exposures.
