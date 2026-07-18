# Source Map — regulatory-reporting-data-validator

## Source hierarchy (highest first)

| Rank | Source (MCP integration) | Used for | Access |
| ---- | ------------------------ | -------- | ------ |
| 1 | **ERP/GL + subledgers + consolidation** (position of record) | Authoritative balances behind reconciliation tie-outs | Read-only |
| 2 | **Regulatory-reporting instructions** (report form, schedule, edit-check spec) | Required cells, declared edit checks, due dates, filing calendar | Read-only |
| 3 | **FP&A / prior filings** | Period-over-period variance baseline, restatement context | Read-only |
| 4 | **Reporting workflow / sign-off log** | Preparer / reviewer / approver evidence, timestamps, roles | Read-only |
| 5 | Regulatory-reporting **config** (versioned) | Thresholds, tolerances, required roles, priority mapping | Read-only |

The reported value never overrides the GL. If a reported cell and the GL conflict, cite both
and raise a reconciliation break; do not adjust either silently. Regulatory instructions
(cells, edit checks, due dates) are a versioned contract — cite the instruction version used.

## Citation format

`{system}:{ref}@{period}` — e.g. `gl:acct=GL-LN;entity=RSSD-***4567@2026-06-30`,
`recon:R2@2026-06-30`, `editcheck:EC2@2026-06-30`, `signoff:approver@2026-07-16T10:00:00`.
Every fired finding cites the specific cell(s), reconciliation, edit check, or sign-off row
it is based on, plus the basis (threshold/tolerance/expected value).

## Freshness / effective dates

- **Config** (thresholds, tolerances, required roles, mapping) is a **versioned contract**;
  the output records the `config_version` so a validation run is reproducible.
- **Reporting instructions** are versioned per reporting period; record which instruction
  version defined the cells/edit checks.
- **Reconciliation source values** must be as-of the reporting `period_end`; a source value
  from a different close is `not_evaluable`, not a tie.
- **Prior period** must be the correct comparative period; note any restatement.

## Least-privilege operations (deployment)

- `gl.balance(entity, account, period_end)` → authoritative balance for a tie-out.
- `reporting.instructions(report_code, period_end)` → required cells + edit-check spec + due date.
- `filings.prior(report_code, prior_period)` → prior-period cell values (+ restatement flag).
- `workflow.signoffs(report_code, period_end)` → sign-off roles + timestamps.
- `config.get('reg-reporting', version)` → thresholds, tolerances, required roles, mapping.

All read-only, deterministic, durable `validation_id`, and below the fixed timeout; page long
cell sets as resumable stages. No write, posting, sign-off, or submission operation is bound.
