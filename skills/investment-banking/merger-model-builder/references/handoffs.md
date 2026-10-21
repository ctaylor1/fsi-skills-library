# Adjacent-Skill Handoffs — merger-model-builder

This skill builds a deterministic pro forma **model** (`model_id`) and stops. It does not
value the companies, opine on fairness, package a pitch, or recommend a transaction.

## Upstream (feed this skill)

| Upstream skill | Provides | Consumed as |
| -------------- | -------- | ----------- |
| `three-statement-model-builder` | Standalone acquirer/target projections | Net income, shares by period |
| `dcf-modeler` | Intrinsic valuation reference for the offer | Context for premium/consideration |
| `comps-analysis-builder` | Trading/transaction multiples | Context for the offer range |
| `earnings-results-analyzer` | Latest reported results | Standalone financial inputs |
| `company-profile-builder` | Acquirer/target profiles | Entity and structure context |

## Downstream (route the analyst/reviewer to)

| Downstream skill | When | Handoff artifact |
| ---------------- | ---- | ---------------- |
| `scenario-sensitivity-generator` | Deeper multi-driver scenario/sensitivity work | `model_id` + drivers |
| `lbo-model-builder` | The structure is a financial-sponsor LBO (IRR/MOIC), not a strategic merger | Deal drivers |
| `investment-banking-pitch-builder` | The model goes into a client pitch | `model_id` + output table |
| `due-diligence-packager` | The model supports a diligence package | `model_id` + assumptions |
| `coverage-meeting-preparer` | The model supports a coverage/committee meeting | `model_id` + summary |

## Human / licensed-specialist handoffs (no skill substitutes for these)

- **Valuation / fairness opinion** — whether the consideration is fair, or what a company is
  worth, is a **licensed valuation/fairness specialist** judgment. This skill provides the
  mechanical pro forma only and routes the opinion to that specialist and the deal team.
- **Purchase-accounting sign-off** — final goodwill/intangible allocation is an accounting
  specialist's determination; the model uses preliminary estimates, labelled as such.
- **Deal decision** — whether to pursue, price, or approve the transaction stays with the deal
  team and the relevant committee.

## Duplicate-execution prevention

- This skill computes the pro forma **model only**; it must not value the companies, opine on
  fairness, or recommend a transaction — those belong to licensed humans and the deal team.
- Downstream pitch/diligence/scenario skills reuse the `model_id` and its assumptions rather
  than rebuilding the pro forma, so a single sourced model flows through the deliverables.
