# Source Map — transaction-reconciliation-helper

## Source hierarchy (highest first)

Reconciliation matches the same transaction across systems. Authority differs by *what* is
being established: the bank record is the position of record for **cash actually moved**;
the processor/acquirer is authoritative for **card capture detail and fees**; the ledger is
the **internal book** being tied out.

| Rank | Source (MCP integration) | Authoritative for | Access |
| ---- | ------------------------ | ----------------- | ------ |
| 1 | **Bank** (DDA / funding account) | Cash actually received/paid (position of record for cash) | Read-only |
| 2 | **Processor / acquirer** settlement detail | Capture amount, fees, interchange, chargeback/refund status | Read-only |
| 3 | **Gateway** authorization record | Auth/capture lifecycle, order reference | Read-only |
| 4 | **Ledger** (GL / ERP) | Internal recorded amount being reconciled | Read-only |
| 5 | **Merchant order** system | Expected order amount, SKU/tax context | Read-only |
| 6 | Reconciliation **config** (versioned) | Tolerances, expected sources, cash ranking | Read-only |

Cash position of record = the highest-ranked present source in `config.cash_rank`
(default `bank > processor > gateway`). Never treat the ledger as the cash position of
record; the ledger is the side being tied out.

## Citation format

`{source}:{source_ref}@{date}` — e.g. `bank:bank=dda;id=B-1003@2026-07-13`. Every break and
every routed break cites the specific source rows behind it; every proposed entry references
its `txn_ref`.

## Freshness / effective dates

- Config (tolerances, expected sources, ranking) is a **versioned contract**; the output
  records the `config_version` so a reconciliation is reproducible.
- Cash lands after capture: bank rows legitimately post 1–2 days (`intransit_days`) after the
  gateway/processor rows. A cash source missing *within* the in-transit window is a timing
  reconciling item, not a confirmed break — flag for confirmation, do not adjust.
- Reconcile a bounded period (`as_of` and the record set); state the window in the output.

## Least-privilege operations (deployment)

- `gateway.read(period)` / `processor.read(period)` / `bank.read(period)` → bounded, paged
  transaction rows.
- `ledger.read(period)` → GL lines for the same period.
- `refdata.resolve(merchant|fee_schedule)` → normalized merchant/fee context.
- `config.get('recon', version)` → tolerances, expected sources, cash ranking.

All read-only, deterministic, durable `recon_id`, below the fixed timeout; page long periods
as resumable stages. No operation writes, posts, or submits — proposed entries leave this
skill as drafts for a human and the ledger system.
