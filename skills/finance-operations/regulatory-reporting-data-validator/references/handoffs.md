# Adjacent-Skill Handoffs — regulatory-reporting-data-validator

This skill produces a cited **validation findings pack** (`validation_id`) with a readiness
band and stops. It does not correct, assemble, certify, sign off, file, or submit.

## Upstream (may call this skill / feed inputs)

| Upstream skill | Provides | Handoff artifact |
| -------------- | -------- | ---------------- |
| `gl-reconciler` | GL-to-subledger reconciliation results that back the tie-out evidence | reconciliation set + source balances |
| `financials-normalizer` | Inconsistent source statements normalized into model-ready, provenance-tagged data | normalized cells + mappings |
| `month-end-close-orchestrator` | The close context that requests validation as a gated step (R4 orchestrator; it, not this skill, gates postings/sign-offs) | package + due date |

## Downstream (route the human/reviewer to)

| Downstream skill | When | Handoff artifact |
| ---------------- | ---- | ---------------- |
| `gl-reconciler` | A reconciliation break needs a proposed journal correction (for approval) | `validation_id` + break rows |
| `management-reporting-packager` | The validated numbers are assembled into a controlled report package with commentary | `validation_id` + cleared cells |
| `audit-evidence-packager` | The validation evidence + sign-off trail is packaged with chain of custody | `validation_id` + findings + evidence |
| `financial-statement-audit-assistant` | Audit tie-out/testing support over the same figures | `validation_id` + cited cells |
| `regulatory-exam-response-packager` | A regulator/examiner asks about the filing and a controlled response package is needed | `validation_id` + findings |
| `transaction-reporting-quality-checker` | The request is actually transaction/trade-report validation, not report-package validation | report scope + fields |

## Duplicate-execution prevention

- This skill computes and evidences **findings and a readiness band only**; it must not
  correct data, assemble the package, certify, sign off, file, or submit — those belong to
  the human preparer/approver and the downstream skills.
- Downstream skills reuse the `validation_id` findings/evidence rather than re-running the
  checks; `gl-reconciler` owns the journal-correction proposal, not this skill.
- A scheduled monitor is **not** used here (interactive skill, `aws-fsi-scheduled-agent: no`).
