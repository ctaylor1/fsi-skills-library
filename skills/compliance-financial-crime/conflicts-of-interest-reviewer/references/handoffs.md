# Adjacent-Skill Handoffs — conflicts-of-interest-reviewer

This skill produces a cited **conflicts evidence pack** (`review_id`) — indicators, affected
parties, incentives, control gaps, residual risk, and a recommended review path — and stops.
It does not adjudicate, clear, waive, close, or file.

## Downstream (route the human/reviewer to)

| Downstream skill | When | Handoff artifact |
| ---------------- | ---- | ---------------- |
| `employee-trading-preclearance-assistant` | The matter involves a specific proposed personal trade needing preclearance against restricted lists, holdings, and blackout windows (gated action) | `review_id` + the personal_trading finding |
| `suitability-reg-bi-reviewer` | The conflict arises in a client **recommendation** and needs best-interest/Reg BI review of costs, alternatives, and disclosures | `review_id` + affected recommendation |
| `surveillance-alert-triager` → `market-surveillance-alert-investigator` | Facts suggest possible MNPI misuse, insider dealing, or an information-barrier breach needing trade/e-comms surveillance | `review_id` + information_barrier / personal_trading findings |
| `policy-procedure-gap-analyzer` | The review reveals a conflicts **policy or procedure gap** to remediate | open-gap list + config version |
| `risk-control-self-assessment-assistant` | Residual conflict risk feeds RCSA scoring and **remediation tracking** | `review_id` + residual risk + open gaps |
| `regulatory-exam-response-packager` | The conflicts evidence must be organized into an **exam/inquiry** response package | `review_id` + evidence pack |
| `adverse-media-investigator` | A counterparty needs credible **adverse-media** assessment for context | counterparty identity |

## Upstream (may call this skill)

`suitability-reg-bi-reviewer` may request a conflicts screen on a recommendation, and
compliance intake / case-management workflows may request a conflicts pack for a disclosed
matter. A scheduled monitor is **not** used here (this skill is interactive,
`aws-fsi-scheduled-agent: no`).

## Human / specialist hand-off (no catalog skill)

The **adjudication itself** — clearing, waiving, restricting, escalating, closing, or filing —
is a qualified human's decision (compliance officer, legal counsel, or the conflicts/ethics
committee, per residual risk). There is no catalog skill for that decision, and this skill must
route to the human rather than simulate the outcome.

## Duplicate-execution prevention

- This skill computes and evidences **indicators and residual risk only**; it must not reach a
  disposition, contact the subject, or take/recommend a binding action — those belong to the
  human adjudicator and the downstream skills.
- Downstream skills reuse the `review_id` evidence rather than re-classifying the matter.
