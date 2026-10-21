# Adjacent-Skill Handoffs — due-diligence-packager

Packaging (this skill) is separated from modeling, valuation, profiling, and process
tracking. It produces cited inputs and hands them off; it does not perform the downstream
work. Every referenced skill below exists in `catalog/skills-catalog.json`.

## Downstream (this skill hands off to)

| Downstream skill | When | Handoff artifact |
| ---------------- | ---- | ---------------- |
| `three-statement-model-builder` | Extracted financials are ready to feed an integrated model | `pack_id` + financial extraction bundle (cited) |
| `dcf-modeler` | A DCF is to be built from the cited financials | `pack_id` + financial extraction bundle + drivers |
| `lbo-model-builder` | Sponsor/LBO analysis is requested | `pack_id` + financial + debt-related extractions |
| `merger-model-builder` | Accretion/dilution or pro-forma work is requested | `pack_id` + financial extraction bundle |
| `comps-analysis-builder` | Operating metrics feed comparable-company analysis | `pack_id` + operating-metric extractions (cited) |
| `scenario-sensitivity-generator` | Scenario/sensitivity ranges are needed on the model | `pack_id` + base-case extraction bundle |
| `company-profile-builder` | A profile / strip page is needed alongside the pack | `pack_id` + business-overview extractions |
| `transaction-process-tracker` | Open questions/issues feed the deal process & follow-ups | `pack_id` + open-questions + issue log |

Model-handoff targets emitted by `calculate_or_transform.py` are validated against the known
modeling-skill set; an unknown target is flagged as an invalid handoff rather than emitted.

## Upstream (feeds this skill)

- The **data room / VDR** provides the raw documents; `transaction-process-tracker` may
  indicate which diligence request items and access grants are in place. This skill is
  **interactive** (`aws-fsi-scheduled-agent: no`); no scheduled agent triages or acts here.

## Human / operations handoffs (no catalog skill)

- **External delivery** of the pack to a counterparty or client is performed by a **human deal
  lead** after recorded approval — there is no delivery skill and this skill never sends.
- **Legal / regulatory opinions** on flagged issues (e.g., change-of-control, litigation)
  route to **licensed counsel**, not to any skill.
- **Valuation / fairness opinions** are a **human, licensed** deliverable; this skill neither
  values nor advises.

## Duplicate-execution prevention

- This skill **does not** build models, compute valuations, profile companies, or track the
  deal process — those belong to the named downstream skills.
- Downstream modeling consumes the `pack_id`/bundle rather than re-extracting from the VDR.
- Approval and delivery are recorded once in the ledger; the packager never marks itself
  approved or delivered.
