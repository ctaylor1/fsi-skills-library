# Adjacent-Skill Handoffs — margin-collateral-optimizer

This skill produces a cited **collateral-allocation recommendation** (`recommendation_id`)
and stops. It does not pledge, move, substitute, or settle collateral, and it does not
dispute or accept a margin call. Those are human/authorized-system actions that happen
**after** treasury and operations approve the recommendation.

## Downstream (route the reviewer to, after approval + execution)

| Downstream skill | When | Handoff artifact |
| ---------------- | ---- | ---------------- |
| `post-trade-settlement-monitor` | Track settlement of the approved collateral movements | `recommendation_id` + posted assets |
| `settlement-break-reconciler` | A collateral movement fails or breaks in settlement | posted assets + expected vs actual |
| `counterparty-exposure-monitor` | Rising counterparty/CCP exposure drives or follows the call | portfolio + counterparty |
| `liquidity-risk-scenario-analyzer` | Assess the funding/liquidity impact of the plan under stress | recommended allocation + funding estimate |
| `corporate-action-election-assistant` | A pledged/eligible security faces a corporate action affecting eligibility or requiring substitution | affected asset + agreement |

## Upstream (may lead into this skill)

`counterparty-exposure-monitor` may flag exposure that prompts a collateral review, and a
treasury/collateral-operations analyst may request a recommendation interactively. There is
no scheduled monitor here (`aws-fsi-scheduled-agent: no`).

## Human / operations handoff (no catalog skill performs these)

The **actual instruction to pledge, post, substitute, or settle collateral**, any
**dispute, acceptance, or rejection of a margin call**, and any **binding funding decision**
(repo, borrow/lend, FX to raise cash) are performed by **treasury and collateral operations**
in the collateral-management and settlement systems — not by any skill. This skill supplies
the analysis those humans approve and act on.

## Duplicate-execution prevention

- This skill computes and evidences an **allocation recommendation only**; it must not reach
  a binding decision, contact the counterparty, or take/stage a collateral action.
- Downstream skills reuse the `recommendation_id` and the approved allocation rather than
  recomputing it, and own their own case states (settlement, break, exposure).
