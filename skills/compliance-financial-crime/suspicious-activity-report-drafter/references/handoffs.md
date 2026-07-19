# Adjacent-Skill Handoffs — suspicious-activity-report-drafter

SAR drafting is a **draft-and-package** control activity. It sits **downstream** of a
human-adjudicated transaction-monitoring investigation and **upstream** of SAR quality review,
MLRO/BSA compliance approval, and human filing. It never re-adjudicates the case, decides
suspicion, or files.

## Upstream (feeds this skill)

| Upstream skill | Provides | Handoff artifact |
| -------------- | -------- | ---------------- |
| `transaction-monitoring-alert-investigator` | The concluded, adjudicated investigation whose findings warrant a SAR draft | `case_id` + approving investigation + findings/rationale |
| `enhanced-due-diligence-packager` | An EDD case whose adjudication surfaced reportable suspicion | `case_id` + evidence package |
| `aml-alert-triager` | Further upstream: the escalation that became the investigation (never drafts a SAR from triage) | escalated `case_id` |

A SAR draft is only produced from a case **approved/adjudicated for SAR drafting**. If the
case is not approved (`case_approved_for_sar` is false), this skill fails closed: `blocked`,
routed back to `transaction-monitoring-alert-investigator` to conclude the investigation.

## Specialist corroboration (this skill routes to, then packages the result)

| Skill | When | Handoff artifact |
| ----- | ---- | ---------------- |
| `sanctions-match-adjudicator` | A potential sanctions match surfaces on a subject during drafting | `case_id` + screening result |
| `adverse-media-investigator` | New adverse-media hits need corroboration before the narrative is final | `case_id` + media hits |
| `beneficial-ownership-verifier` | Ownership/control of an entity subject needs verification | `case_id` + ownership evidence |
| `customer-risk-rating-reviewer` | Drafting surfaces a rating/trigger question | `customer_id` + trigger evidence |

## Downstream (human quality review, approval, and filing)

The completed draft package is handed to the **SAR quality reviewer** and the **MLRO / BSA
Officer**, who quality-review the narrative, decide whether to file, and — if filing — e-file
the SAR via **BSA E-Filing**. These are **human/operations** steps: there is no catalog skill
that files a SAR, and this skill never initiates a filing, sets a filing status of record, or
closes the case.

## Duplicate-execution prevention

- This skill **does not** investigate, adjudicate suspicion, decide file/no-file, adjudicate
  sanctions, disposition adverse media, verify UBO, change a risk rating, close the case, or
  file — those belong to the named skills or the human quality reviewer / MLRO / BSA Officer.
- Investigator and specialist outputs are consumed as **cited evidence**; they are not re-run
  inside this skill.
- The package carries a durable `case_id`; the quality reviewer and filer act on the package
  rather than re-drafting it.
