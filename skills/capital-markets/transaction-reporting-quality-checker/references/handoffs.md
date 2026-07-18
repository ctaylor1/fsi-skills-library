# Adjacent-Skill Handoffs — transaction-reporting-quality-checker

This skill produces a cited **reporting-exception pack** (`qc_id`) and stops. It does not
repair trade records, validate the input pipeline, decide compliance, or file anything.

## Downstream (route the human/reviewer to)

| Downstream skill | When | Handoff artifact |
| ---------------- | ---- | ---------------- |
| `trade-break-resolver` | An exception is really a trade-record break across systems needing an approved, lineage-tracked repair (R4) | `qc_id` + exception refs |
| `regulatory-reporting-data-validator` | The defect is upstream in the report input transformations / controls, not the trade data | `qc_id` + exception codes |
| `market-surveillance-alert-investigator` | The anomaly suggests potential market abuse rather than a data-quality defect (first-line `surveillance-alert-triager`) | focal txns + evidence |
| `regulatory-exam-response-packager` | Exceptions and evidence must be assembled into an examination / inquiry response package | `qc_id` + evidence |
| `best-execution-reviewer` | The real question is execution quality / venue / routing, not reporting quality | executions + period |

## Upstream (may call this skill)

`post-trade-settlement-monitor` may surface settlement fails that drive reporting-completeness
gaps and queue a QC review; a reporting/operations analyst also runs this skill interactively.
A scheduled monitor is **not** used here (this skill is interactive,
`aws-fsi-scheduled-agent: no`).

## Human / licensed-specialist handoff (no catalog skill)

The actual **submission, amendment, cancellation, or suppression** of a regulatory report,
any **compliance/breach determination**, and any **self-report to a regulator** are performed
by a licensed compliance officer or authorized reporting-operations human — there is no skill
in the library that files or amends regulatory reports, and this skill must never do so.

## Duplicate-execution prevention

- This skill computes and evidences **exceptions only**; it must not repair, validate the
  input pipeline, determine compliance, or file — those belong to the humans and the
  downstream skills above.
- Downstream skills reuse the `qc_id` evidence rather than recomputing the QC checks.
