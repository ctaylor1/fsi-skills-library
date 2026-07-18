# Adjacent-Skill Handoffs — fpa-variance-analyzer

This skill produces a cited **variance-analysis pack** (`analysis_id`) with draft commentary
and stops. It does not package the board report, reconcile the ledger, post a correction,
commit a forecast, or make a management decision.

## Downstream (route the human/reviewer to)

| Downstream skill | When | Handoff artifact |
| ---------------- | ---- | ---------------- |
| `management-reporting-packager` | The reviewed commentary is ready to assemble into a controlled management/board report with KPI narrative and lineage | `analysis_id` + material findings |
| `gl-reconciler` | A variance looks like a posting error / GL-to-subledger break needing reconciliation and a proposed correction | line + evidence |
| `financial-statement-audit-assistant` | Auditors need the variance evidence mapped for testing | `analysis_id` + citations |
| `audit-evidence-packager` | The variance evidence must be indexed and preserved with chain of custody | `analysis_id` + evidence rows |
| `valuation-reviewer` | A variance is driven by a fair-value/valuation question rather than operating performance | line + evidence |
| `regulatory-reporting-data-validator` | The variance concerns regulatory-report inputs and their controls/reconciliations | line + citations |

Posting a correcting journal or gating a sign-off is not this skill's job — those belong to
`gl-reconciler` (proposal) and `month-end-close-orchestrator` (posting/certification), each
with its own approval gate.

## Upstream (may call this skill)

| Upstream skill | Why |
| -------------- | --- |
| `financials-normalizer` | Actuals and plan on inconsistent charts of accounts are mapped/standardized first, then handed here for variance analysis |
| `month-end-close-orchestrator` | The close process requests variance analysis as a close task; this skill returns evidence, not a posting |

A scheduled monitor is **not** used here (this skill is interactive,
`aws-fsi-scheduled-agent: no`).

## Decisions that are not a skill handoff (route to a human)

- **Management decisions** (headcount, program funding, budget approval) → the finance
  business partner and management own these; the skill supplies evidence, not the decision.
- **Forecast/guidance commitment** → the FP&A leadership and approved company-communication
  process; never committed by this skill.

## Duplicate-execution prevention

- This skill computes and evidences **variances and draft commentary only**; it must not
  package the final report, reconcile, post, commit a forecast, or decide — those belong to
  the downstream skills and the human.
- Downstream skills reuse the `analysis_id` evidence rather than recomputing variances.
