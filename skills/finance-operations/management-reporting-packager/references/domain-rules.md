# Domain Rules — management-reporting-packager

Orientation references: the firm's management-reporting / disclosure-controls standard and
its approved report template and reporting config take precedence and are **versioned
contracts**. Figures follow the firm's basis of preparation (US GAAP by default; configure
additional jurisdiction/basis packs per deployment). The rules below are configuration, not
judgment — thresholds and required roles come from the versioned config.

## Variance computation (deterministic)

For each KPI with a baseline:

| Measure | Formula |
| ------- | ------- |
| Variance vs budget | `value - budget` (and `%` of budget) |
| Variance vs prior | `value - prior` (and `%` of prior) |

A percentage is reported only when the baseline is non-zero. A KPI with neither budget nor
prior yields `not-computable` variances (a warning, not a block) — the figure still needs a
citation.

## Support status (the unsupported-claim rule)

| Condition | support_status |
| --------- | -------------- |
| Figure has a `source_ref` **and** any commentary has a `commentary_source_ref` | `supported` |
| Figure missing `source_ref`, **or** commentary present without `commentary_source_ref` | `unsupported` |

An `unsupported` KPI is a blocking reason. Commentary is a *claim*: it needs its own citation
even when the figure is cited. Never paraphrase a number the sources do not contain.

## Reconciliation tie-out (deterministic)

`difference = ledger_balance - subledger_balance`. Tie-out is `tie` when
`abs(difference) <= tolerance` (per-reconciliation `tolerance`, else the package-level
`reporting_tolerance`), otherwise `break`. Any `break` is a blocking reason and is routed to
`gl-reconciler`; the pack records it as unresolved and never nets or explains it away.

## Required approvals

`preparer` and `reviewer` sign-offs must be **recorded** (status in
`recorded | complete | signed`) before a package may be `ready-for-review`. The `delivery`
approval is a **human/operations** action and remains `pending` — this skill never records
it. Recording delivery here is a control breach.

## Package status (deterministic)

`package_status = blocked` if **any** blocking reason exists:

- one or more `unsupported` KPIs;
- one or more reconciliation `break`s;
- no reconciliations provided at all;
- a missing required approval (`preparer` or `reviewer`).

Otherwise `package_status = ready-for-review`. `delivery_status` is **always** `draft`.

## Hard boundaries (fail closed)

- No **delivery, submission, distribution, or posting** of the pack; draft-only.
- No **final / board-approved / certified** marking of any figure; no recording delivery
  approval.
- No **unsupported claims**; every figure and commentary line is cited or it blocks.
- No **override** of a reconciliation break beyond tolerance.
- No **forward-looking guarantees or investment advice**.

## Required package contents (the eight template sections)

Cover & reporting scope; Executive takeaways; KPI scorecard & commentary; Reconciliation &
tie-out summary; Source lineage & citations; Exceptions & data gaps; Approvals & sign-off
log; Standing note & distribution control. All eight are enforced by `validate_output.py`.
