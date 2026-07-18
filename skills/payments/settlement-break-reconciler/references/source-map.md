# Source Map — settlement-break-reconciler

## Source hierarchy (highest first)

Settlement reconciliation has **two anchors**: the network/scheme file is authoritative for
what was *cleared*, and the bank cash record is authoritative for what was *received*. The
processor file is the working ledger between them; the internal ledger is what the firm
*booked*. Cite every break to the specific source rows it came from.

| Rank | Source (MCP integration) | Authoritative for | Access |
| ---- | ------------------------ | ----------------- | ------ |
| 1 | **Bank cash** settlement (DDA/nostro statement) | Cash actually received (funding) | Read-only |
| 2 | **Network/scheme** settlement files (Visa, Mastercard, Amex, etc.) | Gross cleared per scheme | Read-only |
| 3 | **Acquirer/processor** settlement files | Gross, fees, reserve, net (the working breakdown) | Read-only |
| 4 | **Fee & reserve schedule** (contracted rates, versioned) | Expected fees and reserves | Read-only |
| 5 | **Internal ledger / subledger** (GL) | What the firm posted | Read-only |

Never substitute the processor's net for the bank cash record when testing cash tie-out, and
never substitute an internal ledger entry for the settlement file when testing completeness.
When two sources conflict, cite both and classify the break — do not silently pick one.

## Matching key

Records are matched across sources by `match_key` (a stable settlement identifier — e.g.
`settlement_date + scheme + batch/funding reference`). At deployment the key is derived by
the entity-resolution service; the bundled fixtures carry an explicit `match_key` so matching
is deterministic and testable. Currency is compared per matched group (`CURRENCY_MISMATCH`).

## Citation format

`{system}:{source_ref}@{date}` — e.g. `processor:proc=ACQ1;batch=B-0703-VISA@2026-07-03`,
`bank_cash:bank=DDA123;fund=B-0704-AMEX@2026-07-05`. Every break and every proposed
correction cites the specific evidence rows behind it (lineage).

## Freshness / effective dates

- The **fee/reserve schedule** and **tolerance config** are versioned contracts; the output
  records `config_version` so a reconciliation is reproducible.
- The reconciliation is bounded to a `period` (start/end). Settlements cleared within
  `cash_settlement_lag_days` of `period.end` with no cash yet are **timing differences**
  (in-transit reconciling items), not missing-cash breaks.
- The `reconciliation_id` binds the output to the inputs + config version; re-running the
  same inputs reproduces the same breaks and the same `correction_id`s (idempotency).

## Least-privilege operations (deployment)

- `settlement.read(scheme, period)` → paged network settlement rows.
- `processor.read(acquirer, period)` → paged processor settlement rows.
- `bankcash.read(account, period)` → cash receipts.
- `ledger.read(account, period)` → posted settlement entries.
- `schedule.get('fees', version)` → contracted fee/reserve rates.

All read-only, deterministic, durable `reconciliation_id`, below the fixed timeout; page long
periods as resumable stages. **No** posting, journal write, or system-of-record mutation is
in scope — corrections are proposed for a human/authorized process (see controls.md).
