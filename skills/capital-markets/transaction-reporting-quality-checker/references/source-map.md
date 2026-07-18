# Source Map — transaction-reporting-quality-checker

## Source hierarchy (highest first)

| Rank | Source (MCP integration) | Used for | Access |
| ---- | ------------------------ | -------- | ------ |
| 1 | Front-office **OMS/EMS executions** (position of record) | Economic terms, execution timestamp, `reportable` flag — the truth a report is measured against | Read-only |
| 2 | **Regulatory-reporting / ARM archive** | The submitted reports, their status, and submission timestamps | Read-only |
| 3 | **Reference data** | LEI, ISIN, MIC resolution and format/validity | Read-only |
| 4 | Post-trade / clearing | Settlement/confirmation cross-checks for completeness | Read-only |
| 5 | Reporting **config** (versioned) | Deadline, required fields, identifier formats, economic fields, tolerances, unresolved statuses | Read-only |

Never treat the submitted report as the position of record. When the report and the source
execution conflict, the conflict **is** the exception — cite both sides and flag it.

## Citation format

`{system}:{ref}@{timestamp}` — e.g. `oms:oms=OMS1;exec=E-4@2026-07-14T11:00:00` for a source
execution and `arm:arm=ARM1;rpt=R-4@2026-07-14T15:00:00` for a submitted report. Every
exception cites the specific source and/or report rows behind it. Economic mismatches cite
**both** sides (`citation_source` and `citation_report`).

## Freshness / effective dates

- Config (deadline, required fields, formats, tolerances) is a **versioned contract**; the
  output records the `config_version` so a QC run is reproducible.
- Reference data (LEI/ISIN/MIC) is time-sensitive; record the effective snapshot used so a
  later re-run does not silently re-classify an identifier.
- Timeliness is computed against the regime's reporting clock; normalize timestamps to that
  clock and cut-off calendar before computing lag.

## Least-privilege operations (deployment)

- `oms.executions(batch_id | date, regime)` → bounded, paged execution rows incl. `reportable`.
- `reporting.reports(batch_id | date, regime)` → submitted reports, status, submission time.
- `refdata.resolve(lei | isin | mic)` → normalized identifier + validity.
- `config.get('txn-report', regime, version)` → deadline, required fields, formats, tolerances.

All read-only, deterministic, durable `qc_id`, below the fixed timeout; page long batches as
resumable stages. No operation submits, amends, cancels, or suppresses a report.
