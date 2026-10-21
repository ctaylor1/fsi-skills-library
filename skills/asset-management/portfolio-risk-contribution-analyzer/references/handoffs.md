# Adjacent-Skill Handoffs — portfolio-risk-contribution-analyzer

This skill produces a source-linked **risk-contribution packet** (`packet_id`) — computed
ex-ante total risk, its Euler decomposition into marginal (MCR), total (TRC), and percentage
(PCR) contributions per position and group, a reconciliation to the approved risk engine total,
and the material changes since the prior review — and stops. It does **not** set a risk limit,
mandate or recommend a portfolio action, make a mandate-compliance determination, or deliver the
packet anywhere.

## The named adjacency (exposures vs risk contributions)

`portfolio-exposure-analyzer` and this skill are deliberately adjacent and must not duplicate
each other:

| Question | Skill | Artifact |
| -------- | ----- | -------- |
| *How much am I exposed to X?* (absolute exposure by issuer/sector/country/currency/duration/liquidity, look-through) | `portfolio-exposure-analyzer` | `exposure_id` |
| *How much of my risk comes from X?* (marginal/total/percentage risk contribution) | `portfolio-risk-contribution-analyzer` (this skill) | `packet_id` |

A large weight (exposure) is not the same as a large risk contribution — correlation and
volatility reweight it. Route absolute-exposure questions to `portfolio-exposure-analyzer`; route
risk-decomposition questions here.

## Upstream (feed this skill)

| Upstream skill / source | Provides | Handoff artifact |
| ----------------------- | -------- | ---------------- |
| PMS/OMS holdings (platform service) | Approved portfolio weights + grouping labels | Positions with weights |
| Approved risk model (platform service) | Annualized covariance matrix + methodology/version | Covariance + methodology |
| Approved risk engine (platform service) | Official ex-ante total risk (reconciliation anchor) | `approved_engine.total_risk` |
| Prior approved packet (packet store) | Baseline decomposition | `prior_packet_id` |

## Parallel / cross-check

| Skill | Why |
| ----- | --- |
| `portfolio-exposure-analyzer` | Absolute-exposure view alongside the risk-contribution view |
| `portfolio-stress-test-runner` | Scenario/stress loss attribution (scenarios from `stress-test-scenario-designer`) |
| `fund-liquidity-assessor` | Liquidation-horizon / redemption-coverage risk |
| `portfolio-performance-attributor` | Return attribution (allocation/selection/factor), not risk |

## Downstream (consume this skill's `packet_id`)

| Downstream skill | When | Handoff artifact |
| ---------------- | ---- | ---------------- |
| `investment-committee-memo-builder` | The decomposition becomes evidence in an IC / risk-committee memo | `packet_id` + contribution summary |
| `investment-mandate-reviewer` | A human tests contributions/utilization against mandate guidelines | `packet_id` + contributions |
| `market-risk-limit-monitor` | Ongoing limit / VaR / breach monitoring and escalation | `packet_id` + total + contributions |
| `fund-fact-sheet-builder` | A risk-concentration summary feeds a fact sheet | `packet_id` + group contributions |

## Human / governance handoff (no skill substitutes for it)

- **Risk-limit decisions** — setting, changing, calibrating, or approving any risk limit,
  risk-appetite threshold, or utilization cap — belong to the **risk committee / limits-
  governance owner**. **No skill in this library sets limits.** This skill routes limit
  questions to that human body; it never sets or proposes a limit.
- **Portfolio actions** — any trade, rebalance, hedge, or de-risking — belong to the
  **portfolio manager** under human authorization; this skill never recommends or executes one.
- **Mandate-compliance determinations** (breach / no-breach) belong to
  `investment-mandate-reviewer` and a **human compliance officer**.
- **Personalized investment advice** is a licensed-human matter.

## Duplicate-execution prevention

- This skill builds and ties out the **decomposition only**; it must not compute absolute
  exposures (that is `portfolio-exposure-analyzer`), reach a compliance determination, set a
  limit, or take an action.
- Downstream skills reuse the `packet_id` (with its `inputs_hash` and `config_version`) rather
  than recomputing the decomposition, so the same inputs produce the same numbers everywhere
  the packet is cited.
