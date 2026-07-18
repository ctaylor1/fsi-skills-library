# Adjacent-Skill Handoffs — lbo-model-builder

This skill produces a source-linked **LBO model** (`model_id`) — Sources & Uses, a
per-tranche debt schedule with cash sweep, a levered free-cash-flow forecast, liquidity, an
exit walk, sponsor returns (MOIC / IRR), and base / upside / downside cases with tie-outs —
and stops. It does not issue an investment recommendation, guarantee a return, approve a
deal, or deliver the model anywhere.

## Upstream (feed this skill)

| Upstream skill | Provides | Handoff artifact |
| -------------- | -------- | ---------------- |
| `three-statement-model-builder` | Linked operating model whose forecast drives the levered FCF | Driver set + base-year financials |
| `financials-normalizer` | Normalized historicals (adjusted EBITDA, one-off-clean margins) | Clean LTM base lines |
| `financial-spreading-assistant` | Standardized spread of filed statements | Historical statement lines |
| `company-profile-builder` | Business/segment context for driver reasonableness | Company profile |
| `earnings-results-analyzer` | Latest quarter actuals and guidance deltas | Updated near-term drivers |
| `comps-analysis-builder` | Entry/exit EV/EBITDA multiples and sector leverage norms | Multiple + leverage inputs |
| `market-sizing-builder` / `market-landscape-researcher` | TAM / growth context behind revenue drivers | Growth assumptions |

## Parallel / cross-check

| Skill | Why |
| ----- | --- |
| `dcf-modeler` | Intrinsic-value cross-check (unlevered DCF) against the return-based LBO |
| `comps-analysis-builder` | Relative-valuation cross-check (trading comps) on entry and exit |
| `merger-model-builder` | Alternative transaction lens (accretion/dilution) for the same target |
| `scenario-sensitivity-generator` | Expand cases into full entry-multiple / leverage / exit sensitivity grids |

## Downstream (consume this skill's `model_id`)

| Downstream skill | When | Handoff artifact |
| ---------------- | ---- | ---------------- |
| `valuation-reviewer` | Independent review of the finished model for errors/reasonableness | `model_id` + assumptions register |
| `investment-committee-memo-builder` | The LBO returns become evidence in an IC memo | `model_id` + returns summary |
| `investment-banking-pitch-builder` | Financing/returns page in a pitch or CIM | `model_id` + returns + capital structure |
| `due-diligence-packager` | Model attached to a diligence package | `model_id` + assumptions register |
| `board-committee-pack-builder` | Returns section of a board pack | `model_id` + scenario summary |
| `coverage-initiation-researcher` | LBO feasibility anchors a take-private / sponsor-interest thesis | `model_id` + narrative |

## Human / licensed-specialist handoff (no skill substitutes for it)

The **investment decision** — whether to make, hold, or exit the investment, commit capital,
approve the deal at investment committee, or offer a fairness opinion — is **out of scope**
and belongs to the **deal team, the investment committee, or a licensed
valuation/fairness-opinion specialist**. This skill routes that decision to those humans; it
never makes it. Personalized investment, legal, or tax advice is likewise a licensed-human
matter.

## Duplicate-execution prevention

- This skill builds and ties out the **model only**; it must not reach a recommendation,
  guarantee a return, approve a deal, or deliver the model — those belong to humans and
  downstream skills.
- Downstream skills reuse the `model_id` (with its `inputs_hash` and `config_version`)
  rather than rebuilding the debt schedule or returns, so the same assumptions produce the
  same numbers everywhere the model is cited.
