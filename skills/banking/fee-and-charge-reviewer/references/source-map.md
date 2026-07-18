# Source Map — fee-and-charge-reviewer

## Source hierarchy (highest first)

| Rank | Source (MCP integration) | Used for | Access |
| ---- | ------------------------ | -------- | ------ |
| 1 | **Product terms / fee schedule** (controlled content, versioned) | Disclosed fee amounts, caps, waiver conditions — the comparison basis | Read-only |
| 2 | Core-banking **fee/charge postings** (position of record) | Posted fees actually assessed on the account | Read-only |
| 3 | **CRM** / account context | Waiver conditions met (direct deposit, minimum balance, account type), prior contact | Read-only |
| 4 | **Loan origination/servicing** (when the charge is loan-side) | Loan-level fees, late charges, servicing terms | Read-only |
| 5 | Fee-review **config** (versioned) | Amount tolerance and comparison parameters | Read-only |

The **disclosed schedule is the comparison basis**, and the **posting is the record of what
was charged**. Never substitute a customer assertion, a marketing summary, or a prior schedule
version for the disclosed term in effect for the statement period. If the posting and the
disclosed term conflict, that is the finding — cite both; do not resolve it silently or
declare which is "correct".

## Citation format

`{system}:{ref}[@{date}]` — e.g. posted `fees:acct=****4321;feeid=F-6@2026-06-10`; disclosed
`terms:doc=fee-schedule-2026-01;sec=atm`. Every flagged finding cites the posted row and, when
a disclosed term exists, the disclosed term it was compared against.

## Freshness / effective dates

- The fee schedule is a **versioned contract**; the output records the schedule/`config_version`
  used so a review is reproducible. Use the schedule **in effect for the statement period**,
  not merely the latest one.
- State the exact `statement_period` compared in the output.

## Least-privilege operations (deployment)

- `terms.get(product, effective_date)` → disclosed fee schedule (amounts, caps, waiver conditions).
- `fees.read(account_id, period_start, period_end)` → posted fee/charge rows.
- `crm.context(account_id)` → waiver-condition status (direct deposit, balance, account type).
- `config.get('fee-review', version)` → tolerance + comparison parameters.
All read-only, deterministic, durable `review_id`, below the fixed timeout; page long
statement histories as resumable stages.
