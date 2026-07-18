# Source Map — fpa-variance-analyzer

## Source hierarchy (highest first)

| Rank | Source (MCP integration) | Used for | Access |
| ---- | ------------------------ | -------- | ------ |
| 1 | **ERP/GL + consolidation** (position of record) | Posted actuals by account / cost center / period | Read-only |
| 2 | **Subledgers** (AP, AR, payroll, inventory) | Detail behind a GL line when a driver needs decomposition | Read-only |
| 3 | **FP&A / planning system** | Budget, forecast, and prior-period figures; approved driver decompositions | Read-only |
| 4 | Materiality & attribution **config** (versioned) | Thresholds, run-rate escalation, tie-out tolerance, periods remaining | Read-only |
| 5 | **Document/spreadsheet** intelligence | Commentary templates, prior narratives (context only, never the number of record) | Read-only |

Posted **actuals** in the GL/consolidation are the position of record. Never substitute a
forecast, an accrual estimate, a spreadsheet, or a prior narrative for the posted actual. If
the GL and the planning system disagree on what "actual" or "plan" is, cite both and flag the
conflict for the reviewer — do not silently pick one.

## Citation format

`{system}:{source_ref}#{field}@{period}` — e.g. `gl:gl=cons;acct=5000;cc=COGS#actual@2026-06`.
Driver rows cite the FP&A decomposition source: `fpa:{source_ref}#driver@{period}`. Every
material finding cites the actual and the compared base, plus any driver rows behind the
attribution.

## Freshness / effective dates

- Materiality thresholds, run-rate escalation, and tie-out tolerance are a **versioned
  contract** (`config_version`); the output records the version so an analysis is reproducible.
- Actuals must be from a **closed or explicitly stated soft-close** period; label the close
  status. Variances computed against an open period are provisional.
- State the exact `basis` (budget / forecast / prior) that drives the materiality screen; the
  other two comparisons are reported for context.

## Least-privilege operations (deployment)

- `gl.actuals(entity, period, accounts[])` → posted actuals by line.
- `fpa.plan(entity, period, basis)` → budget / forecast / prior figures and approved drivers.
- `subledger.detail(account, period)` → decomposition detail on request (bounded, paged).
- `config.get('fpa-materiality', version)` → thresholds + escalation + tolerance.

All read-only, deterministic, durable `analysis_id`, below the fixed timeout; page long
account sets as resumable stages. No write, posting, or forecast-commit operation is bound.
