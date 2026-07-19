# Adjacent-Skill Handoffs — enhanced-due-diligence-packager

EDD packaging is a **draft-and-package** control activity. It sits between first-line
screening/triage (upstream) and human adjudication (downstream of this skill), and it pulls
corroboration from specialist skills. It never performs their work or the adjudicator's.

## Upstream (feeds this skill)

| Upstream skill | Provides | Handoff artifact |
| -------------- | -------- | ---------------- |
| `kyc-customer-due-diligence-screener` | CDD result that triggers EDD (high-risk classification) | `customer_id` + trigger + CDD evidence |
| `customer-risk-rating-reviewer` | A High risk rating / trigger requiring EDD | `customer_id` + rating rationale |
| `aml-alert-triager` | An escalation whose customer needs an EDD refresh | `case_id` + escalation context |

## Specialist corroboration (this skill routes to, then packages the result)

| Skill | When | Handoff artifact |
| ----- | ---- | ---------------- |
| `beneficial-ownership-verifier` | Ownership is layered/opaque/nominee | `case_id` + ownership evidence to verify |
| `adverse-media-investigator` | Adverse-media severity is moderate/severe | `case_id` + media hits to disposition |
| `sanctions-match-adjudicator` | A sanctions true-match indicator (hard boundary → `blocked`) | `case_id` + screening result |

## Downstream (human adjudication + regulated follow-on)

The completed draft package is handed to the **human adjudicator** (EDD investigator, MLRO/BSA
Officer, senior management as configured) who decides the relationship, changes any rating of
record, and authorizes any follow-on. Only **after** an adjudicated outcome may a suspicion
warrant `suspicious-activity-report-drafter` (draft-only, human-filed). This skill never
initiates a filing.

## Duplicate-execution prevention

- This skill **does not** verify UBO, disposition adverse media, adjudicate sanctions, decide
  the relationship, change the rating of record, or file — those belong to the named skills or
  the human adjudicator.
- Specialist outputs are consumed as **cited evidence**; the specialists are not re-run inside
  this skill.
- The package carries a durable `case_id`; the adjudicator acts on the package rather than
  re-assembling it.
