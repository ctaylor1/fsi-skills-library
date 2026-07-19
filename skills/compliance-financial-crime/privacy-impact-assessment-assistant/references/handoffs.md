# Adjacent-Skill Handoffs — privacy-impact-assessment-assistant

Privacy impact assessment is a **draft-and-package** control activity. It sits between the
intake that flags a processing activity as needing a DPIA (upstream) and the human privacy
sign-off (downstream of this skill), and it pulls corroboration from specialist skills. It
never performs their work or the adjudicator's.

## Upstream (feeds this skill)

| Upstream skill | Provides | Handoff artifact |
| -------------- | -------- | ---------------- |
| `ai-use-case-intake-classifier` | A new AI/data use case classified as high-risk / DPIA-required | use-case id + classification + trigger |
| `regulatory-change-impact-analyzer` | A privacy regulatory change requiring a new or refreshed DPIA | change ref + affected processing |
| `policy-procedure-gap-analyzer` | A policy/procedure gap surfacing a processing that lacks a DPIA | gap ref + processing context |

## Specialist corroboration (this skill routes to, then packages the result)

| Skill | When | Handoff artifact |
| ----- | ---- | ---------------- |
| `data-lineage-documenter` | Large-scale processing or data matching/combining needs end-to-end data-flow mapping | `assessment_id` + processing scope |
| `third-party-risk-assessor` | Processors/sub-processors or an international-transfer recipient are involved | `assessment_id` + recipient/vendor context |
| `ai-risk-assessment-builder` | Automated decision-making with legal/similar effect or novel AI technology | `assessment_id` + model/use-case context |

## Downstream (human sign-off + regulated follow-on)

The completed draft assessment is handed to the **human adjudicator** (Data Protection Officer,
privacy officer, legal/senior management as configured) who signs off the processing, records
any lawful basis of record, and — where a High residual risk cannot be mitigated — decides on
**prior consultation with the supervisory authority** (a human/legal step this skill never
initiates). If the assessment surfaces a live personal-data incident, that is handled by the
relevant **security/privacy incident** operations team, not this skill.

## Duplicate-execution prevention

- This skill **does not** map data lineage, assess third-party risk, build the AI risk
  assessment, approve the processing, set the lawful basis of record, or file — those belong to
  the named skills or the human adjudicator.
- Specialist outputs are consumed as **cited evidence**; the specialists are not re-run inside
  this skill.
- The assessment carries a durable `assessment_id`; the adjudicator acts on the draft rather
  than re-assembling it.
