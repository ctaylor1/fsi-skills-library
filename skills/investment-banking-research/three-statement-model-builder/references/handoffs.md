# Adjacent-Skill Handoffs — three-statement-model-builder

This skill produces an integrated **three-statement operating model** (`model_id`) — a
linked income statement, balance sheet, and cash-flow statement with supporting debt, PP&E,
and working-capital schedules, base/upside/downside scenarios, and independent tie-outs — and
stops. It does not discount the model to a value, issue a recommendation, a price target, or
a fairness opinion, and it does not deliver the model anywhere.

## Upstream (feed this skill)

| Upstream skill | Provides | Handoff artifact |
| -------------- | -------- | ---------------- |
| `financial-spreading-assistant` | Standardized spread of filed statements | Historical base-year statement lines |
| `financials-normalizer` | Normalized historicals (adjusted margins, one-off-clean lines) | Clean base-year income statement |
| `company-profile-builder` | Business/segment context for driver reasonableness | Company profile |
| `earnings-results-analyzer` | Latest quarter actuals and guidance deltas | Updated near-term drivers |
| `market-sizing-builder` / `market-landscape-researcher` | TAM / growth context behind the revenue driver | Growth assumptions |

## Downstream (consume this skill's `model_id`)

| Downstream skill | When | Handoff artifact |
| ---------------- | ---- | ---------------- |
| `dcf-modeler` | Discount the model's free cash flow at a WACC to a value per share | `model_id` + forecast drivers / base-year lines |
| `lbo-model-builder` | Use the operating model as the base case for a leveraged-buyout returns model | `model_id` + operating forecast |
| `merger-model-builder` | Feed the operating forecast into an accretion/dilution analysis | `model_id` + standalone forecast |
| `comps-analysis-builder` | Standardized forecast metrics for a relative-valuation cross-check | `model_id` + forecast metrics |
| `scenario-sensitivity-generator` | Expand the three cases into full driver-vs-margin sensitivity grids | `model_id` + scenario deltas |
| `valuation-reviewer` | Independent review of the finished model for errors/reasonableness | `model_id` + assumptions + tie-outs |
| `investment-committee-memo-builder` | The model becomes evidence in an IC memo | `model_id` + scenario summary |
| `investment-banking-pitch-builder` | Model page in a pitch/CIM | `model_id` + forecast summary |
| `board-committee-pack-builder` | Financial-forecast section of a board pack | `model_id` + scenario summary |
| `due-diligence-packager` | Model attached to a diligence package | `model_id` + assumptions |
| `coverage-initiation-researcher` | The model anchors a coverage-initiation forecast section | `model_id` + narrative |

## Human / licensed-specialist handoff (no skill substitutes for it)

The **investment judgment** — whether the forecast implies buy/sell/hold, a published price
target, a fairness opinion, or any personalized recommendation — is **out of scope** and
belongs to a **licensed research analyst, the deal team, an investment committee, or a
valuation/fairness-opinion specialist**. This skill routes that decision to those humans; it
never makes it. Personalized investment, legal, accounting, audit, or tax advice is likewise
a licensed-human matter.

## Duplicate-execution prevention

- This skill builds and ties out the **operating model only**; it must not discount it to a
  value, reach a recommendation, set a target, or deliver the model — those belong to humans
  and downstream skills.
- Downstream skills reuse the `model_id` (with its `inputs_hash` and `config_version`)
  rather than rebuilding the forecast, so the same assumptions produce the same numbers
  everywhere the model is cited.
