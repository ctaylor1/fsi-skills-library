# Adjacent-Skill Handoffs — portfolio-risk-diversification-check

This skill produces a cited, educational **exposure profile** (`analysis_id`) and stops. It
does not advise, recommend a trade, judge suitability, or write any system of record.

## Downstream (route the reader to)

| Downstream skill | When | Handoff artifact |
| ---------------- | ---- | ---------------- |
| `portfolio-holdings-summarizer` | The user actually wants a plain summary of what is held, not concentration/risk analysis | portfolio + as_of |
| `prospectus-plain-language-breakdown` | The user wants one fund/product explained (fees, strategy, liquidity of a single security) | the security/prospectus |
| `trade-confirmation-explainer` | The user wants a single trade confirmation explained | the confirmation |
| `corporate-action-interpreter` | A holding is subject to a corporate action needing interpretation | the event + position |
| `margin-collateral-optimizer` | The concentration/liquidity question is about **collateral/margin** eligibility and haircuts, not investment diversification | the collateral set |
| **Licensed human financial professional** | The user asks whether to buy/sell/rebalance, whether the portfolio suits them, or for a financial plan | `analysis_id` + the exposure profile as background |

Personalized advice, suitability, and any trade decision are **out of scope for this and every
skill in the library** — route to a licensed human. This skill supplies the analysis as
background only.

## Upstream (may call this skill)

A holdings-review or client-service copilot may request an exposure profile as context. A
scheduled monitor is **not** used here (this skill is interactive,
`aws-fsi-scheduled-agent: no`).

## Duplicate-execution prevention

- This skill computes and evidences **exposure checks only**; it must not reach an
  investment recommendation, a suitability call, or a trade — those belong to a licensed human.
- Downstream/consuming flows reuse the `analysis_id` profile rather than recomputing metrics,
  and must not re-label the educational band as advice.
