# Adjacent-Skill Handoffs — scenario-sensitivity-generator

This skill flexes an **existing** base-case model and emits an analysis pack
(`analysis_id`). It never originates a valuation or adds a recommendation.

## Upstream (provide the base-case model)

| Upstream skill | Handoff artifact |
| -------------- | ---------------- |
| `dcf-modeler` | Base drivers + output formulas (WACC, growth, margins → value) |
| `three-statement-model-builder` | Integrated model drivers + outputs |
| `lbo-model-builder` | Leverage/returns drivers + outputs |
| `merger-model-builder` | Accretion/dilution drivers + outputs |
| `comps-analysis-builder` | Multiple-based implied-value drivers |

## Downstream (embed the pack)

| Downstream skill | When |
| ---------------- | ---- |
| `investment-banking-pitch-builder` | Pack becomes a pitch/exhibit page |
| `company-profile-builder` | Pack supports a profile/strip page |
| `due-diligence-packager` | Pack indexed into the diligence set |

## Lateral / route instead

- Market sizing / TAM driver work with no existing model → `market-sizing-builder`.
- A recommendation, rating, price target, or "is this a good investment" → out of scope;
  route the judgment to a licensed research/deal professional.

## Duplicate-execution prevention

- This skill does not build or re-originate a model, nor assemble a deck/memo — those are
  the upstream modeling and downstream packaging skills.
- Downstream packaging reuses the `analysis_id` pack rather than recomputing tables.
