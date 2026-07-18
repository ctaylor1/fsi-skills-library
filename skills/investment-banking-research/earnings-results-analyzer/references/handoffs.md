# Adjacent-Skill Handoffs — earnings-results-analyzer

This skill produces a cited **earnings-analysis pack** (`analysis_id`) and stops. It does not
build the model, form the investment view, rate the stock, or publish.

## Downstream (route the human/analyst to)

| Downstream skill | When | Handoff artifact |
| ---------------- | ---- | ---------------- |
| `three-statement-model-builder` | Roll the new actuals + revised guidance into the operating model | `analysis_id` + metric/guidance findings |
| `dcf-modeler` | Refresh the intrinsic valuation after estimate/driver changes | `analysis_id` + revised drivers |
| `comps-analysis-builder` | Refresh trading comps/multiples on the post-print figures | `analysis_id` + updated actuals |
| `scenario-sensitivity-generator` | Build scenarios/sensitivities around the revised estimates | `analysis_id` + driver ranges |
| `investment-committee-memo-builder` | A PM wants an IC memo that incorporates the print | `analysis_id` + findings |
| `investment-thesis-monitor` | Ongoing monitoring of whether the print confirms or breaks the thesis | `analysis_id` + thesis considerations |
| `coverage-meeting-preparer` | Prepare coverage/marketing-meeting materials around the results | `analysis_id` + summary |

## Upstream (may call this skill)

`coverage-meeting-preparer` and `coverage-initiation-researcher` may request an earnings read;
a portfolio analyst may invoke it directly. A scheduled monitor is **not** used here (this
skill is interactive, `aws-fsi-scheduled-agent: no`).

## Human / licensed-specialist handoff (no skill performs this)

Forming the **investment view** and issuing a **rating or price target** is the work of the
covering **licensed research analyst** (under supervisory-analyst and compliance review), and
any **portfolio/trade action** belongs to the portfolio manager and the firm's authorized
execution process. There is no catalog skill that rates a stock, sets a target, publishes a
note, or trades — those are deliberately human, supervised steps. This analyzer hands the
cited facts to those people; it does not stand in for them.

## Duplicate-execution prevention

- This skill computes and evidences **classifications only**; it must not build the model,
  reach a rating/target, publish, or trade — those belong to the modeling skills, the human
  analyst/PM, and authorized systems.
- Downstream skills reuse the `analysis_id` findings rather than re-deriving the surprise.
