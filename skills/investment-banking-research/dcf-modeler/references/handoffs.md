# Adjacent-Skill Handoffs — dcf-modeler

This skill produces a source-linked **DCF model** (`model_id`) — forecast, WACC, terminal
value, enterprise-to-equity bridge, three scenarios, and tie-outs — and stops. It does not
issue a recommendation, a price target, or a fairness opinion, and it does not deliver the
model anywhere.

## Upstream (feed this skill)

| Upstream skill | Provides | Handoff artifact |
| -------------- | -------- | ---------------- |
| `three-statement-model-builder` | Linked operating model whose forecast drives the UFCF | Driver set + base-year financials |
| `financials-normalizer` | Normalized historicals (adjusted EBIT, one-off-clean margins) | Clean base-year lines |
| `financial-spreading-assistant` | Standardized spread of filed statements | Historical statement lines |
| `company-profile-builder` | Business/segment context for driver reasonableness | Company profile |
| `earnings-results-analyzer` | Latest quarter actuals and guidance deltas | Updated near-term drivers |
| `market-sizing-builder` / `market-landscape-researcher` | TAM / growth context behind revenue drivers | Growth assumptions |

## Parallel / cross-check

| Skill | Why |
| ----- | --- |
| `comps-analysis-builder` | Relative-valuation cross-check (trading comps) against the DCF |
| `scenario-sensitivity-generator` | Expand scenarios into full WACC-vs-g and driver sensitivity grids |
| `lbo-model-builder` / `merger-model-builder` | Alternative/return-based valuation lenses for the same target |

## Downstream (consume this skill's `model_id`)

| Downstream skill | When | Handoff artifact |
| ---------------- | ---- | ---------------- |
| `valuation-reviewer` | Independent review of the finished model for errors/reasonableness | `model_id` + assumptions register |
| `investment-committee-memo-builder` | The DCF becomes evidence in an IC memo | `model_id` + scenario summary |
| `investment-banking-pitch-builder` | Valuation page in a pitch/CIM | `model_id` + football-field inputs |
| `due-diligence-packager` | Model attached to a diligence package | `model_id` + assumptions register |
| `board-committee-pack-builder` | Valuation section of a board pack | `model_id` + scenario summary |
| `coverage-initiation-researcher` | DCF anchors a coverage-initiation valuation section | `model_id` + narrative |

## Human / licensed-specialist handoff (no skill substitutes for it)

The **investment judgment** — whether the value implies buy/sell/hold, a published price
target, a fairness opinion, or any personalized recommendation — is **out of scope** and
belongs to a **licensed research analyst, the deal team, an investment committee, or a
valuation/fairness-opinion specialist**. This skill routes that decision to those humans; it
never makes it. Personalized investment, legal, or tax advice is likewise a licensed-human
matter.

## Duplicate-execution prevention

- This skill builds and ties out the **model only**; it must not reach a recommendation,
  set a target, or deliver the model — those belong to humans and downstream skills.
- Downstream skills reuse the `model_id` (with its `inputs_hash` and `config_version`)
  rather than rebuilding the forecast, so the same assumptions produce the same numbers
  everywhere the model is cited.
