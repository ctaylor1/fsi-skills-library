# Adjacent-Skill Handoffs — fund-liquidity-assessor

This skill produces a cited **liquidity-stress pack** (`analysis_id`) under stated scenario
assumptions and stops. It does not decide, trade, gate, or determine a breach.

## Downstream (route the human/reviewer to)

| Downstream skill | When | Handoff artifact |
| ---------------- | ---- | ---------------- |
| `investment-mandate-reviewer` | The reviewer needs a mandate/guideline/regulatory liquidity-rule test or a breach finding (human-adjudicated) | `analysis_id` + positions + scenario |
| `counterparty-exposure-monitor` | Collateral/margin needs feed counterparty, settlement, and limit monitoring | `analysis_id` + margin positions |
| `investment-committee-memo-builder` | Package the liquidity-stress findings and scenarios into an IC memorandum | `analysis_id` + metrics + scenarios |
| `investment-commentary-builder` | Liquidity metrics inform periodic fund commentary (product + compliance approved) | `analysis_id` + summary metrics |
| `institutional-proposal-responder` | A DDQ/RFP asks about liquidity risk and stress methodology | `analysis_id` + methodology + metrics |

## Upstream (may provide inputs / call this skill)

`portfolio-exposure-analyzer` supplies position-level exposures (including a liquidity
dimension) that seed this analysis. This skill is **interactive**
(`aws-fsi-scheduled-agent: no`); a scheduled monitor is not used here.

## Human / specialist handoffs (no skill performs these)

- Any **decision to trade, raise cash, gate or suspend redemptions, activate a side pocket,
  or apply swing pricing** belongs to the **portfolio manager, liquidity risk committee, and
  dealing/execution desk** — never this or any skill.
- **Personalized investment, trading, or tax advice** requires a **licensed professional**.

## Duplicate-execution prevention

- This skill computes and evidences **metrics under a stated scenario only**; it must not reach
  a decision, place a trade, take a fund-liquidity action, or issue a breach finding — those
  belong to the human committee, `investment-mandate-reviewer` (breach test), and the execution
  desk.
- Downstream skills reuse the `analysis_id` evidence rather than recomputing the liquidity model.
