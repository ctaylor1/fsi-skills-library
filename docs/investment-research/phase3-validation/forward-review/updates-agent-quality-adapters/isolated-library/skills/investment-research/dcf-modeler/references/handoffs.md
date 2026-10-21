# Adjacent-Skill Handoffs — dcf-modeler

## Version 0.2.0 contract

Only standalone-ratio-fcff forecasting is implemented. This method reforecasts from ratio drivers; it does not consume native three-statement rows or establish identical upstream forecasts. Every equity-bridge component must be explicit, finite, nonnegative and sourced, including genuine zeros; otherwise calculation is withheld. WACC weights must sum to one; invalid discounting/terminal domains fail input validation. No dividend/residual-income, NAV or financial-institution engine is implied.


This skill produces a source-linked **DCF model** (`model_id`) — forecast, WACC, terminal
value, enterprise-to-equity bridge, three scenarios, and tie-outs — and stops. It does not
issue a recommendation, a price target, or a fairness opinion, and it does not deliver the
model anywhere.

## Upstream (feed this skill)

| Upstream skill | Provides | Handoff artifact |
| -------------- | -------- | ---------------- |
| `three-statement-model-builder` | Context for explicitly reviewed standalone assumptions; no forecast-row adapter | Reviewed driver mapping + base-year financials |
| `financials-normalizer` | Normalized historicals (adjusted EBIT, one-off-clean margins) | Clean base-year lines |
| `financial-spreading-assistant` | Standardized spread of filed statements | Historical statement lines |
| `company-profile-builder` | Business/segment context for driver reasonableness | Company profile |
| `earnings-results-analyzer` | Latest quarter actuals and guidance deltas | Updated near-term drivers |
| `market-sizing-builder` / `market-landscape-researcher` | TAM / growth context behind revenue drivers | Growth assumptions |

## Parallel / cross-check

| Skill | Why |
| ----- | --- |
| `comps-analysis-builder` | Relative-valuation cross-check (trading comps) against the DCF |
| `scenario-sensitivity-generator` | Bounded supplied-formula sensitivities only; no native DCF runner adapter |
| `lbo-model-builder` / `merger-model-builder` | Alternative/return-based valuation lenses for the same target |

## Downstream (consume this skill's `model_id`)

| Downstream skill | When | Handoff artifact |
| ---------------- | ---- | ---------------- |
| Human research model reviewer | Review model scope, inputs, formulas and economic assumptions; Finance valuation-reviewer addresses marks/IPV instead | Native result + original input + assumptions register |
| `investment-committee-memo-builder` | The DCF becomes evidence in an IC memo | `model_id` + scenario summary |
| `investment-banking-pitch-builder` | Valuation page in a pitch/CIM | `model_id` + football-field inputs |
| `due-diligence-packager` | Model attached to a diligence package | `model_id` + assumptions register |
| `board-committee-pack-builder` | Valuation section of a board pack | `model_id` + scenario summary |
| `coverage-initiation-researcher` | DCF anchors a coverage-initiation valuation section | `model_id` + narrative |

## Human / licensed-specialist handoff (no skill substitutes for it)

The **investment judgment** — whether the value implies buy/sell/hold, a published price
target, a fairness opinion, or any personalized recommendation — is **out of scope** and
belongs to a **institution-authorized research analyst, the deal team, an investment committee, or a
valuation/fairness-opinion specialist**. This skill routes that decision to those humans; it
never makes it. Personalized investment, legal, or tax advice is likewise a licensed-human
matter.

## Duplicate-execution prevention

- This skill builds and ties out the **model only**; it must not reach a recommendation,
  set a target, or deliver the model — those belong to humans and downstream skills.
- Downstream skills reuse the `model_id` (with its `inputs_hash` and `config_version`)
  as references only; this does not supply a native receiver adapter or prove matching forecasts. Any remapping must be explicit and reviewed.
