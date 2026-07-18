# Source Map — bank-statement-analyzer

## Source hierarchy (highest first)

| Rank | Source (MCP integration) | Used for | Access |
| ---- | ------------------------ | -------- | ------ |
| 1 | Core-banking **statement / transaction ledger** (position of record) | Authoritative transaction rows, running balances, opening/closing balances | Read-only |
| 2 | **Document intelligence** (parsed statement PDF/image) | Statement metadata, page/line provenance when only a document is supplied | Read-only |
| 3 | **CRM** customer context | Known employers/payees, disclosed income sources, life events | Read-only |
| 4 | **Reference / product terms** | Fee schedules, merchant/counterparty resolution, category taxonomy | Read-only |
| 5 | Analysis **config** (versioned) | Categorization keywords, recurrence and anomaly thresholds | Read-only |

When a bank record (ledger) and a parsed document disagree, the **ledger is the position of
record**; cite both and flag the discrepancy for the reviewer. Never substitute a customer
assertion (e.g., "that deposit is my salary") for the record — record and label both.

## Citation format

`{system}:{ref}@{date}` — e.g. `stmt:stmt=****4321;line=L-0007@2026-04-08`. Every extracted
figure (income, obligation, fee, anomaly) cites the specific statement line(s) it derives
from, plus the period window used.

## Freshness / effective dates

- Config (categorization keywords, recurrence and anomaly thresholds) is a **versioned
  contract**; the output records the `config_version` used so an analysis is reproducible.
- The statement period is stated explicitly in the output; figures are scoped to that window.
- If transactions fall outside the stated period, flag them rather than silently including.

## Least-privilege operations (deployment)

- `statements.read(account_id, from, to)` → bounded, paged transaction rows + balances.
- `docintel.parse(statement_id)` → line-level rows with page/line refs (document path only).
- `crm.context(account_id)` → disclosed income sources, known payees (no free-text PII beyond
  what evidences an extracted figure).
- `refdata.resolve(merchant|category|fee_code)` → normalized values and fee schedule.
- `config.get('statement-analysis', version)` → keywords + thresholds.

All read-only, deterministic, durable `analysis_id`, below the fixed timeout; page long
statement histories as resumable stages.
