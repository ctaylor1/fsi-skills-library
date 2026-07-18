# Source Map — management-reporting-packager

## Source hierarchy (highest first)

| Rank | Source (MCP integration) | Used for | Access |
| ---- | ------------------------ | -------- | ------ |
| 1 | **Consolidation / ERP-GL** (system of record) | Reported KPI figures, consolidated balances, close cut-off | Read-only |
| 2 | **Subledgers** (AR, AP, revenue, inventory, fixed assets) | Tie-out balances, aging, transaction-level lineage | Read-only |
| 3 | **FP&A** (planning / variance) | Budget, forecast, prior-period baselines, driver commentary | Read-only |
| 4 | **Regulatory reporting** | Validated regulatory metrics when the pack includes them | Read-only |
| 5 | **Controlled template & content library** | The approved report template, effective-dated boilerplate | Read-only |
| 6 | **Permission / approval broker** | Preparer/reviewer sign-off records; delivery stays human | Read-only |
| 7 | **Reporting config** (versioned) | Tie-out tolerances, required-approval set, KPI definitions | Read-only |

The GL/consolidation figure is authoritative for a KPI value; a subledger is authoritative
for the tie-out. Never substitute an analyst-stated number for the system figure. When a
reported value and its subledger conflict, record both and flag the reconciliation break —
do not pick one.

## Citation format

`{system}:{ref}@{date/version}` — e.g. `erp:GL@2026-06-30;pkg=FIN-CLOSE-06`,
`recon:AR-0630@2026-07-02;skill=gl-reconciler`, `fpa:variance=VAR-0612@2026-07-03`,
`config:mrp-reporting@v2026.07`. Every KPI figure carries a `source_ref`; every commentary
line carries a `commentary_source_ref`; every reconciliation and exception carries its own.

## Freshness / effective dates

- All figures must share the **same close cut-off / period**; a mixed-cut-off pack is a data
  gap, not a draftable pack.
- Baselines (budget/forecast/prior) must come from the **approved plan version** for the
  period; record the plan version in the citation.
- The report **template** and **reporting config** are **versioned contracts**; the
  `config_version` is stamped on every assembled package for reproducibility.

## Least-privilege operations (deployment)

- `gl.read(entity, period)`, `subledger.read(ledger, entity, period)` — read-only, bounded.
- `fpa.read(entity, period, plan_version)` — read-only baselines + driver commentary.
- `template.get('management-report', version)`, `config.get('mrp-reporting', version)` —
  read-only versioned contracts.
- `approvals.read(package_id)` — read-only sign-off records.
No mutation from this skill. The assembled pack is a **draft**; external delivery, posting,
and delivery sign-off are performed by humans/operations outside this skill.
