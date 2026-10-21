# Adjacent-Skill Handoffs - kpi-segment-bridge-builder

## Version 0.2.0 contract

Use only closed historical periods with permitted sourced inputs. Referenced authoritative totals must exist. Unrequested reconciliation is not evaluated and never counts as reconciled; the pack reports partial-or-not-evaluable coverage. Mapping IDs are unique, approved and effective on/before the prior-period end so both bridged periods are covered. Full supplied context, including totals/citations/mappings, affects hashes. The volume-price joint term is a two-factor interaction, not general product-mix attribution.


This skill produces a source-linked **KPI/segment bridge pack** (`pack_id`) - revenue, margin,
volume-price, and segment bridges that decompose the change between **two disclosed periods**,
each component tied to a disclosure and reconciled to the reported totals - and stops. It does
**not** forecast, does **not** normalize accounting beyond approved mappings, and does **not**
deliver the pack anywhere.

## Upstream (feed this skill)

| Upstream skill | Provides | Handoff artifact |
| -------------- | -------- | ---------------- |
| `financials-normalizer` | Inconsistent issuer/deal statements standardized onto a model-ready basis with mappings, adjustments, and tie-outs | Standardized statement lines + approved mapping set |
| `financial-spreading-assistant` | Extracted/spread historical statements with reconciled totals | Historical statement lines |
| `earnings-results-analyzer` | Latest reported quarter actuals, disclosed KPI drivers, guidance deltas | Reported KPI actuals |
| `company-profile-builder` | Business/segment context and disclosed KPI set | Company profile + KPI list |

## Parallel / cross-check

| Skill | Why |
| ----- | --- |
| `comps-analysis-builder` | Cross-check disclosed operating metrics and segment splits against peers |

## Downstream (consume this skill's `pack_id`)

| Downstream skill | When | Handoff artifact |
| ---------------- | ---- | ---------------- |
| `dcf-modeler` | The historical drivers become the base for a forward valuation | `pack_id` + driver history |
| `three-statement-model-builder` | The disclosed segments/KPIs seed a forward operating model | `pack_id` + segment/KPI history |
| `scenario-sensitivity-generator` | Flex the historical volume/price/margin drivers into scenarios | `pack_id` + bridge components |
| `earnings-results-analyzer` | The bridge becomes evidence in a beat/miss note | `pack_id` + bridge summary |
| `coverage-initiation-researcher` | KPI/segment history anchors a coverage-initiation draft | `pack_id` + narrative |
| `investment-banking-pitch-builder` | A KPI/segment bridge page in a pitch/CIM | `pack_id` + bridge summary |
| `due-diligence-packager` | The pack attaches to a diligence package | `pack_id` + assumptions register |
| `valuation-reviewer` | Independent review of the finished bridges for errors/reasonableness | `pack_id` + registers |

## Hard-boundary routing (this skill refuses; route instead)

- **Forecasting / projecting** a KPI, segment, margin, volume, or price forward -> **out of
  scope**. Build the historical bridge here, then route the forward work to `dcf-modeler`,
  `three-statement-model-builder`, or `scenario-sensitivity-generator`. The skill never emits a
  forecast, and any forward-looking `source_type` fails input validation.
- **Normalizing accounting judgment beyond approved mappings** (segment recasts, non-GAAP
  adjustments, restatements not in the approved `mapping_version`) -> **out of scope**. Route to
  `financials-normalizer` (and the firm's accounting-policy owner) to have the mapping approved
  first; only then can the component enter a bridge.

## Human / licensed-specialist handoff (no skill substitutes for it)

The **investment judgment** (whether the KPI trajectory implies buy/sell/hold, a target, or a
valuation conclusion) belongs to a **institution-authorized research analyst, the deal team, or an investment
committee**. **Accounting-judgment approval** (whether a new reclassification or non-GAAP basis
is admissible) belongs to the **controller / accounting-policy / model-governance** function,
which owns the approved `mapping_version`. This skill routes both; it never makes either.

## Duplicate-execution prevention

- This skill builds and ties out the **historical bridge only**; it must not forecast,
  normalize beyond approved mappings, reach a recommendation, or deliver the pack - those belong
  to the humans and skills above.
- Downstream skills reuse the `pack_id` (with its `inputs_hash`, `config_version`, and
  `mapping_version`) rather than re-extracting the KPIs, so the same disclosures produce the
  same bridge everywhere it is cited.
