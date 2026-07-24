# Source Map — loan-interest-fee-calculator

## Source hierarchy (highest first)

| Rank | Source (MCP integration) | Used for | Access |
| ---- | ------------------------ | -------- | ------ |
| 1 | **Executed agreement** (note, credit agreement, participation certificate, fee schedule) | Contract terms: rate basis, day-count convention, fee definitions, participation shares, amortization terms | Read-only |
| 2 | **Approved rate tables** (versioned) | Note rates, index + margin, fee rates in effect on the accrual date | Read-only |
| 3 | **Servicing ledger / transactions** (loan servicing system) | Booked principal balances, posted interest and fees, unapplied/suspense funds, payoff quotes | Read-only |
| 4 | **Approved calculation engine** (sanctioned amortization/settlement engine) | Grand totals to reconcile the recomputation against | Read-only |
| 5 | **Calculation config** (versioned) | Day-count defaults, tie-out tolerance, materiality threshold, formula conventions | Read-only |

A **recomputed figure is only as good as its source.** Every principal, rate, fee, base,
settlement component, participation total, and share must resolve to one of the above with a
dated citation. The **executed agreement outranks the servicing ledger**; where a booked
amount conflicts with the agreement's terms, the agreement anchors the recomputation and the
booked amount becomes a **variance** for human review — never silently adopted.

## Citation format

`{source}:{ref}@{date}` — e.g. `agmt:LN-DEMO-2001 sec 4.2 late fee`,
`rt-2026.06:note-rate LN-DEMO-2001`, `svc:interest posting 2026-07-01`,
`eng:AmortEngine v9 run 2026-07-16`. Each `assumptions_register` entry carries `provenance`
(the source class) and `citation` (the specific ref + date). `scripts/validate_output.py`
rejects any assumption missing either.

## Freshness / effective dates

- **`calc_date`** anchors the accrual windows, the payoff date, and the applicable
  rate-table version; state it in the workbook.
- **`rate_table_version`** is a **versioned contract**; a rate cannot be used without one,
  and versions are never mixed within a workbook.
- **`config_version`** binds tolerances, the materiality threshold, day-count defaults, and
  formulas; the workbook records it for reproducibility.
- The **`inputs_hash`** binds the workbook to the exact numeric inputs; re-running the same
  inputs reproduces the same `calc_id` and numbers.

## Least-privilege operations (deployment)

- `agreement.read(loan_id, section)` → executed terms, fee schedule, participation shares.
- `ratetable.get(version, product, as_of)` → note and fee rates in effect on the date.
- `servicing.read(loan_id, account, period)` → booked balances, postings, unapplied funds.
- `engine.totals(loan_id, as_of)` → approved-engine grand totals for reconciliation.
- `config.get('loan-calc', version)` → day-count defaults, tolerance, materiality, formulas.

All read-only, deterministic, durable `case_id` / `calc_id`, below the fixed timeout. This
skill makes **no writes** — no posting, no approval, no system-of-record change. Delivering
the workbook or the payoff quote, and posting any adjustment, are separate, human-authorized
steps. See [SHARED-SERVICES.md](../../../../docs/SHARED-SERVICES.md) for the platform
services these operations bind to.
