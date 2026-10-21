# Adjacent-Skill Handoffs — portfolio-characteristics-change-monitor

This skill produces a cited **change-and-exception packet** (`packet_id`) comparing two
approved characteristic snapshots, and stops. It does not adjudicate limits, decide
remediation, construct or execute trades, or change any mandate. Those are human /
compliance / portfolio-management actions, supported by the downstream skills below.

## Downstream (route the human/analyst to)

| Downstream skill | When | Handoff artifact |
| ---------------- | ---- | ---------------- |
| `investment-mandate-reviewer` | A characteristic is at or near a supplied mandate reference and the question is "is this a breach / what are the limits" — the **authoritative limit test** (HARD BOUNDARY: this skill never adjudicates the breach) | `packet_id` + routed characteristic(s) + current value |
| `portfolio-exposure-analyzer` | The analyst needs deeper issuer/sector/factor/look-through detail behind an active-weight or factor drift | `packet_id` + portfolio + drifted bucket |
| `fund-liquidity-assessor` | A duration/positioning drift raises a liquidity or liquidation-horizon question | portfolio + positions in question |
| `portfolio-performance-attributor` | The user actually wants return attribution (allocation/selection/factor) rather than characteristic drift | portfolio + benchmark + period |
| `portfolio-rebalancing-assistant` | The portfolio manager decides to construct trades to address the drift (manager-directed remediation) | drifted characteristics + targets (human-directed) |
| `investment-committee-memo-builder` | An exception must be escalated into an IC decision memo | `packet_id` + exception evidence |
| `portfolio-holdings-summarizer` | The user wants a plain holdings/positioning summary, not a prior→current drift comparison | portfolio + as-of |

## Upstream (may call this skill)

An interactive portfolio-risk analyst invokes this skill on demand. It is **not** a scheduled
agent (`aws-fsi-scheduled-agent: no`); periodic mandate testing is
`investment-mandate-reviewer`'s job, and this skill consumes/produces packets on request.

## Duplicate-execution prevention

- This skill computes and evidences **changes and exceptions only**; it must not adjudicate a
  mandate breach, direct or size a trade, or change a limit — those belong to the human
  reviewer, `investment-mandate-reviewer`, and the remediation skills.
- Limit adjudication is **not duplicated** here: any at/near-limit characteristic is routed to
  `investment-mandate-reviewer` with the `packet_id`, rather than this skill deciding a breach.
- Downstream skills reuse the `packet_id` change/exception evidence rather than re-computing
  the drift.
