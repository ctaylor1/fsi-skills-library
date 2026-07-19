# Adjacent-Skill Handoffs — retirement-income-scenario-modeler

This skill produces a source-linked **retirement-income projection** (`model_id`) — a
year-by-year decumulation model with base / favorable / adverse scenarios, shortfall/depletion
behavior, and tie-outs — and stops. It does not recommend a strategy, guarantee an outcome,
review suitability, or deliver or execute anything.

## Upstream (feed this skill)

| Upstream skill | Provides | Handoff artifact |
| -------------- | -------- | ---------------- |
| `financial-goal-progress-analyzer` | Whether the household is on track vs. stated goals under approved assumptions | Goal + assumption set, cash flows |
| `investment-policy-statement-builder` | Objectives, risk tolerance, liquidity, and tax constraints that bound the model | IPS constraints |
| `portfolio-proposal-comparator` | The proposed portfolio whose returns/costs feed the projection | Proposal + assumptions |

## Parallel / cross-check

| Skill | Why |
| ----- | --- |
| `portfolio-risk-diversification-check` | Risk/diversification cross-check on the portfolio behind the return assumptions |
| `senior-investor-protection-screener` | Runs in parallel where the client is a senior / vulnerable investor |
| `model-risk-documenter` | Model-governance documentation of the assumptions and methodology |

## Downstream (consume this skill's `model_id`)

| Downstream skill | When | Handoff artifact |
| ---------------- | ---- | ---------------- |
| `suitability-reg-bi-reviewer` | The projection becomes evidence in a suitability / Reg BI review of a recommendation | `model_id` + scenario range |
| `client-review-preparer` | The scenarios anchor the retirement section of a client-review brief/deck | `model_id` + summary |
| `advisor-follow-up-assistant` | Meeting notes, action items, and client communications reference the range | `model_id` + narrative |
| `portfolio-rebalancing-assistant` | Turning the funding plan into a proposed, authorization-gated trade list (R4) | `model_id` + funding needs |

## Human / licensed-specialist handoff (no skill substitutes for it)

The **planning judgment** — whether the client should retire at a given age, when to claim
Social Security, whether to annuitize or convert, what withdrawal rate to adopt, or whether a
product is appropriate — is **out of scope** and belongs to a **licensed financial advisor and
the client**, informed by a **suitability / Reg BI review**. Personalized **tax** guidance
belongs to a CPA / tax advisor, **insurance/annuity** guidance to a licensed insurance
professional, and **estate** questions to an estate attorney. This skill routes those
decisions to those humans; it never makes them, guarantees an outcome, or writes a system of
record.

## Duplicate-execution prevention

- This skill builds and ties out the **model only**; it must not reach a recommendation,
  guarantee an outcome, review suitability, or deliver/execute — those belong to humans and
  downstream skills.
- Downstream skills reuse the `model_id` (with its `inputs_hash` and `config_version`) rather
  than rebuilding the projection, so the same assumptions produce the same numbers everywhere
  the model is cited.
